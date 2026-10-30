package main

import (
	"fmt"
	"unicode/utf8"
)

// A deliberately non-executing subset of protocol 4. No GLOBAL, STACK_GLOBAL,
// REDUCE, BUILD, persistent IDs, imports, or object construction is supported.
// Metadata containers need identity for memo references, but their contents are
// not needed. Only integer -> (text, metadata, metadata) pairs are retained.
type textDict struct{ texts map[uint32]string }
type pickleList struct{}
type pickleMark struct{}
type pickleTuple []any

func localization(b []byte) (map[uint32]string, error) {
	var stack, memo []any
	pos, steps := 0, 0
	take := func(n int) ([]byte, error) {
		if n < 0 || n > len(b)-pos {
			return nil, fmt.Errorf("truncated pickle at byte %d", pos)
		}
		s := b[pos : pos+n]
		pos += n
		return s, nil
	}
	push := func(v any) { stack = append(stack, v) }
	mark := func() int {
		for i := len(stack) - 1; i >= 0; i-- {
			if _, ok := stack[i].(pickleMark); ok {
				return i
			}
		}
		return -1
	}
	set := func(d any, k, v any) error {
		dict, ok := d.(*textDict)
		if !ok {
			return fmt.Errorf("pickle SETITEM on non-dictionary")
		}
		if id, ok := k.(int64); ok && id >= 0 && id <= 0xffffffff {
			if tuple, ok := v.(pickleTuple); ok && len(tuple) == 3 {
				if s, ok := tuple[0].(string); ok {
					dict.texts[uint32(id)] = s
				}
			}
		}
		return nil
	}
	if len(b) < 2 || b[0] != 0x80 || b[1] != 4 {
		return nil, fmt.Errorf("expected localization pickle protocol 4")
	}
	for pos < len(b) {
		steps++
		if steps > 5_000_000 || len(stack) > 1_000_000 || len(memo) > 1_000_000 {
			return nil, fmt.Errorf("pickle resource limit exceeded")
		}
		op := b[pos]
		pos++
		switch op {
		case 0x80:
			v, e := take(1)
			if e != nil {
				return nil, e
			}
			if pos != 2 || v[0] != 4 {
				return nil, fmt.Errorf("unexpected pickle protocol")
			}
		case 0x95:
			v, e := take(8)
			if e != nil {
				return nil, e
			}
			if le.Uint64(v) > uint64(len(b)-pos) {
				return nil, fmt.Errorf("truncated pickle frame")
			}
		case 0x8c, 'X':
			n := 0
			if op == 0x8c {
				v, e := take(1)
				if e != nil {
					return nil, e
				}
				n = int(v[0])
			} else {
				v, e := take(4)
				if e != nil {
					return nil, e
				}
				n = int(le.Uint32(v))
			}
			if n > 1<<20 {
				return nil, fmt.Errorf("pickle string exceeds limit")
			}
			v, e := take(n)
			if e != nil {
				return nil, e
			}
			if !utf8.Valid(v) {
				return nil, fmt.Errorf("invalid pickle UTF-8")
			}
			push(string(v))
		case 'J', 'K', 'M':
			n := 4
			if op == 'K' {
				n = 1
			} else if op == 'M' {
				n = 2
			}
			v, e := take(n)
			if e != nil {
				return nil, e
			}
			var x int64
			switch n {
			case 1:
				x = int64(v[0])
			case 2:
				x = int64(le.Uint16(v))
			case 4:
				x = int64(int32(le.Uint32(v)))
			}
			push(x)
		case 'N':
			push(nil)
		case '}':
			push(&textDict{texts: make(map[uint32]string)})
		case ']':
			push(&pickleList{})
		case '(':
			push(pickleMark{})
		case 0x94:
			if len(stack) == 0 {
				return nil, fmt.Errorf("empty pickle memo stack")
			}
			memo = append(memo, stack[len(stack)-1])
		case 'h', 'j':
			n := 1
			if op == 'j' {
				n = 4
			}
			v, e := take(n)
			if e != nil {
				return nil, e
			}
			i := uint32(v[0])
			if n == 4 {
				i = le.Uint32(v)
			}
			if uint64(i) >= uint64(len(memo)) {
				return nil, fmt.Errorf("invalid pickle memo reference")
			}
			push(memo[i])
		case 0x86, 0x87:
			n := 2
			if op == 0x87 {
				n = 3
			}
			if len(stack) < n {
				return nil, fmt.Errorf("pickle tuple underflow")
			}
			t := append(pickleTuple(nil), stack[len(stack)-n:]...)
			stack = stack[:len(stack)-n]
			push(t)
		case 's':
			n := len(stack)
			if n < 3 {
				return nil, fmt.Errorf("pickle SETITEM underflow")
			}
			if e := set(stack[n-3], stack[n-2], stack[n-1]); e != nil {
				return nil, e
			}
			stack = stack[:n-2]
		case 'u':
			i := mark()
			if i < 1 || (len(stack)-i-1)%2 != 0 {
				return nil, fmt.Errorf("invalid pickle SETITEMS")
			}
			for j := i + 1; j < len(stack); j += 2 {
				if e := set(stack[i-1], stack[j], stack[j+1]); e != nil {
					return nil, e
				}
			}
			stack = stack[:i]
		case 'e':
			i := mark()
			if i < 1 {
				return nil, fmt.Errorf("invalid pickle APPENDS")
			}
			if _, ok := stack[i-1].(*pickleList); !ok {
				return nil, fmt.Errorf("pickle APPENDS on non-list")
			}
			stack = stack[:i]
		case '.':
			if len(stack) != 1 || pos != len(b) {
				return nil, fmt.Errorf("invalid pickle termination")
			}
			root, ok := stack[0].(pickleTuple)
			if !ok || len(root) != 2 {
				return nil, fmt.Errorf("unexpected localization root")
			}
			lang, ok := root[0].(string)
			if !ok || lang != "en-us" {
				return nil, fmt.Errorf("unexpected localization language")
			}
			d, ok := root[1].(*textDict)
			if !ok {
				return nil, fmt.Errorf("missing localization dictionary")
			}
			return d.texts, nil
		default:
			return nil, fmt.Errorf("unsupported/unsafe pickle opcode 0x%02x at byte %d", op, pos-1)
		}
	}
	return nil, fmt.Errorf("pickle has no STOP")
}
