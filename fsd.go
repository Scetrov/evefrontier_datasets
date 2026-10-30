package main

import (
	"bytes"
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"math"
	"unicode/utf8"
)

// These are schema fingerprints, not content hashes. Unknown layouts must fail closed.
const typesSchema = "8d7a099712d997ddc7b0f218c5c8a396d1fb3c55fb466fb7"
const iconsSchema = "e62746ff0dc540cc73e06fca63926f292c4c4dd698322566"
const graphicsSchema = "2bdea664c47b290277ceb9741651e981b6527e41cc25db80"
const groupsSchema = "122e735a97700cf0466ace3d160636438139f2a8f7afc858"
const categoriesSchema = "c5de77dba3d9503eb69b6378c15dd47abd38f8cc9a4373bd"

var le = binary.LittleEndian

type typeRecord struct {
	ID, NameID, IconID, GraphicID, DescriptionID, GroupID uint32
	MarketGroupID                                         *uint32
	Mass, Volume, Capacity, BasePrice                     float64
	PortionSize                                           uint32
}

type groupRecord struct{ ID, CategoryID, NameID uint32 }
type categoryRecord struct{ ID, NameID uint32 }

// cFSD pointers are relative to the payload at byte 32. A dictionary has an
// entry count, then a counted vector of pointers to counted collision buckets.
func fsdEntries(b []byte, schema string, stride int) (map[uint32][]byte, error) {
	return fsdEntriesKeySize(b, schema, stride, 8)
}

func fsdEntriesKeySize(b []byte, schema string, stride, keySize int) (map[uint32][]byte, error) {
	if (keySize != 4 && keySize != 8) || stride < keySize {
		return nil, fmt.Errorf("invalid FSD entry layout")
	}
	sig, _ := hex.DecodeString(schema)
	if len(b) < 56 || !bytes.Equal(b[:24], sig) {
		return nil, fmt.Errorf("unsupported FSD schema (expected %s)", schema)
	}
	if le.Uint64(b[24:]) != uint64(len(b)-32) || le.Uint64(b[32:]) != 24 {
		return nil, fmt.Errorf("invalid FSD header")
	}
	expected, buckets := le.Uint64(b[40:]), le.Uint64(b[48:])
	if expected > 1_000_000 || buckets > uint64((len(b)-56)/8) {
		return nil, fmt.Errorf("invalid FSD table size")
	}
	result := make(map[uint32][]byte)
	for i := uint64(0); i < buckets; i++ {
		ptr := le.Uint64(b[56+i*8:])
		if ptr == 0 {
			continue
		}
		if ptr < 8 || ptr > uint64(len(b)-32) {
			return nil, fmt.Errorf("invalid FSD bucket pointer")
		}
		start := ptr + 32
		count := le.Uint64(b[start-8:])
		if count > expected || count > uint64(len(b)-int(start))/uint64(stride) {
			return nil, fmt.Errorf("invalid FSD bucket size")
		}
		for j := uint64(0); j < count; j++ {
			p := start + j*uint64(stride)
			key := uint64(le.Uint32(b[p:]))
			if keySize == 8 {
				key = le.Uint64(b[p:])
				if key > 0xffffffff {
					return nil, fmt.Errorf("invalid FSD key")
				}
			}
			if _, exists := result[uint32(key)]; exists {
				return nil, fmt.Errorf("duplicate FSD key %d", key)
			}
			result[uint32(key)] = b[p+uint64(keySize) : p+uint64(stride)]
		}
	}
	if uint64(len(result)) != expected {
		return nil, fmt.Errorf("FSD entry count mismatch")
	}
	return result, nil
}

func readTypes(b []byte) ([]typeRecord, int, error) {
	entries, err := fsdEntries(b, typesSchema, 144)
	if err != nil {
		return nil, 0, err
	}
	var out []typeRecord
	for id, v := range entries {
		if le.Uint32(v[112:]) != id {
			return nil, 0, fmt.Errorf("FSD type ID mismatch for %d", id)
		}
		flags := le.Uint32(v[132:])
		if v[129] > 1 {
			return nil, 0, fmt.Errorf("invalid published boolean")
		}
		if flags&(1<<13) == 0 || v[129] == 0 {
			continue
		}
		t := typeRecord{ID: id, NameID: le.Uint32(v[116:]), GroupID: le.Uint32(v[80:]),
			BasePrice: math.Float64frombits(le.Uint64(v)), Capacity: math.Float64frombits(le.Uint64(v[8:])),
			Mass: math.Float64frombits(le.Uint64(v[16:])), Volume: math.Float64frombits(le.Uint64(v[56:])),
			PortionSize: le.Uint32(v[24:])}
		for _, number := range []float64{t.BasePrice, t.Capacity, t.Mass, t.Volume} {
			if math.IsNaN(number) || math.IsInf(number, 0) {
				return nil, 0, fmt.Errorf("non-finite type value for %d", id)
			}
		}
		if flags&(1<<2) != 0 {
			t.DescriptionID = le.Uint32(v[64:])
		}
		if flags&(1<<7) != 0 {
			id := le.Uint32(v[88:])
			t.MarketGroupID = &id
		}
		if flags&(1<<5) != 0 {
			t.IconID = le.Uint32(v[84:])
		}
		if flags&(1<<4) != 0 {
			t.GraphicID = le.Uint32(v[76:])
		}
		out = append(out, t)
	}
	return out, len(entries), nil
}

func readGroups(b []byte) (map[uint32]groupRecord, error) {
	entries, err := fsdEntriesKeySize(b, groupsSchema, 32, 4)
	if err != nil {
		return nil, err
	}
	out := make(map[uint32]groupRecord, len(entries))
	for id, v := range entries {
		if le.Uint32(v[4:]) != id {
			return nil, fmt.Errorf("FSD group ID mismatch for %d", id)
		}
		out[id] = groupRecord{ID: id, CategoryID: le.Uint32(v), NameID: le.Uint32(v[8:])}
	}
	return out, nil
}

func readCategories(b []byte) (map[uint32]categoryRecord, error) {
	entries, err := fsdEntries(b, categoriesSchema, 40)
	if err != nil {
		return nil, err
	}
	out := make(map[uint32]categoryRecord, len(entries))
	for id, v := range entries {
		if le.Uint32(v[8:]) != id {
			return nil, fmt.Errorf("FSD category ID mismatch for %d", id)
		}
		out[id] = categoryRecord{ID: id, NameID: le.Uint32(v[12:])}
	}
	return out, nil
}

func fsdString(b []byte, ptr uint64) (string, error) {
	if ptr < 8 || ptr > uint64(len(b)-32) {
		return "", fmt.Errorf("invalid FSD string pointer")
	}
	p := ptr + 32
	n := le.Uint64(b[p-8:])
	if n > uint64(len(b))-p || n > 1<<20 {
		return "", fmt.Errorf("invalid FSD string length")
	}
	s := b[p : p+n]
	if !utf8.Valid(s) {
		return "", fmt.Errorf("invalid FSD UTF-8")
	}
	return string(s), nil
}

func readIcons(b []byte) (map[uint32]string, error) {
	entries, err := fsdEntries(b, iconsSchema, 32)
	if err != nil {
		return nil, err
	}
	out := make(map[uint32]string)
	for id, v := range entries {
		// iconFile is the first pointer; bit zero marks it present.
		if le.Uint32(v[20:])&1 == 0 {
			continue
		}
		s, e := fsdString(b, le.Uint64(v))
		if e != nil {
			return nil, e
		}
		out[id] = s
	}
	return out, nil
}

func readGraphicFolders(b []byte) (map[uint32]string, error) {
	entries, err := fsdEntries(b, graphicsSchema, 168)
	if err != nil {
		return nil, err
	}
	out := make(map[uint32]string)
	for id, v := range entries {
		if le.Uint32(v[156:])&(1<<9) == 0 || le.Uint32(v[56:])&1 == 0 {
			continue
		}
		s, e := fsdString(b, le.Uint64(v[48:]))
		if e != nil {
			return nil, e
		}
		out[id] = s
	}
	return out, nil
}
