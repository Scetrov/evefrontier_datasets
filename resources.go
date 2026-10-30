package main

import (
	"crypto/md5" // Client index uses MD5 for corruption detection, not authentication.
	"encoding/csv"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"path"
	"regexp"
	"strconv"
	"strings"
)

const maxResource = 64 << 20

var cacheName = regexp.MustCompile(`^[0-9a-f]{2}/[0-9a-f]{16}_[0-9a-f]{32}$`)

type resource struct {
	URI, Cache, MD5 string
	Size            int64
}
type game struct {
	root      *os.Root
	resources map[string]resource
	reads     map[string]string
}

func readLimited(root *os.Root, name string) ([]byte, error) {
	f, e := root.Open(name)
	if e != nil {
		return nil, e
	}
	defer f.Close()
	info, e := f.Stat()
	if e != nil {
		return nil, e
	}
	if !info.Mode().IsRegular() || info.Size() > maxResource {
		return nil, fmt.Errorf("not a regular resource or exceeds 64 MiB: %s", name)
	}
	b, e := io.ReadAll(io.LimitReader(f, maxResource+1))
	if len(b) > maxResource {
		return nil, fmt.Errorf("resource exceeds 64 MiB")
	}
	return b, e
}

func parseIndex(b []byte) (map[string]resource, error) {
	reader := csv.NewReader(strings.NewReader(string(b)))
	reader.FieldsPerRecord = -1
	result := make(map[string]resource)
	for {
		row, e := reader.Read()
		if e == io.EOF {
			break
		}
		if e != nil {
			return nil, e
		}
		if len(row) != 5 && len(row) != 6 {
			return nil, fmt.Errorf("invalid index field count")
		}
		if !cacheName.MatchString(row[1]) {
			return nil, fmt.Errorf("invalid cache path for %q", row[0])
		}
		digest, e := hex.DecodeString(row[2])
		if e != nil || len(digest) != 16 {
			return nil, fmt.Errorf("invalid resource digest")
		}
		n, e := strconv.ParseInt(row[3], 10, 64)
		if e != nil || n < 0 {
			return nil, fmt.Errorf("invalid resource size")
		}
		uri := strings.ToLower(row[0])
		if !strings.HasPrefix(uri, "res:/") && !strings.HasPrefix(uri, "app:/") {
			return nil, fmt.Errorf("invalid resource URI")
		}
		r := resource{URI: uri, Cache: row[1], MD5: strings.ToLower(row[2]), Size: n}
		if old, ok := result[uri]; ok && old != r {
			return nil, fmt.Errorf("conflicting index entry %s", uri)
		}
		result[uri] = r
	}
	return result, nil
}

func (g *game) load(r resource) ([]byte, error) {
	b, e := readLimited(g.root, "ResFiles/"+r.Cache)
	if e != nil {
		return nil, e
	}
	if int64(len(b)) != r.Size {
		return nil, fmt.Errorf("resource size mismatch: %s", r.URI)
	}
	sum := fmt.Sprintf("%x", md5.Sum(b))
	if sum != r.MD5 {
		return nil, fmt.Errorf("resource checksum mismatch: %s", r.URI)
	}
	g.reads[r.URI] = sum
	return b, nil
}
func (g *game) get(uri string) ([]byte, error) {
	r, ok := g.resources[uri]
	if !ok {
		return nil, fmt.Errorf("resource not indexed: %s", uri)
	}
	return g.load(r)
}

func openGame(dir string) (*game, error) {
	root, e := os.OpenRoot(dir)
	if e != nil {
		return nil, e
	}
	g := &game{root: root, resources: make(map[string]resource), reads: make(map[string]string)}
	fail := func(e error) (*game, error) { root.Close(); return nil, e }
	b, e := readLimited(root, "index_stillness.txt")
	if e != nil {
		return fail(e)
	}
	g.reads["index_stillness.txt"] = fmt.Sprintf("%x", md5.Sum(b))
	app, e := parseIndex(b)
	if e != nil {
		return fail(e)
	}
	// Follow only the resource indexes identified by the selected Stillness app index.
	for _, name := range []string{"app:/resfileindex.txt", "app:/resfileindex_windows.txt"} {
		r, ok := app[name]
		if !ok {
			return fail(fmt.Errorf("missing %s in index_stillness.txt", name))
		}
		b, e := g.load(r)
		if e != nil {
			return fail(e)
		}
		rows, e := parseIndex(b)
		if e != nil {
			return fail(e)
		}
		for k, v := range rows {
			if old, ok := g.resources[k]; ok && old != v {
				return fail(fmt.Errorf("conflicting resource indexes: %s", k))
			}
			g.resources[k] = v
		}
	}
	return g, nil
}

var resolutionSuffix = regexp.MustCompile(`_(?:16|32|64|128|256|512|1024|2048|4096)$`)

func iconFamily(uri string) string {
	ext := path.Ext(uri)
	return resolutionSuffix.ReplaceAllString(strings.TrimSuffix(uri, ext), "")
}
