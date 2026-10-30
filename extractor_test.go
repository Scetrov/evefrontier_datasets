package main

import (
	"bytes"
	"crypto/sha256"
	"database/sql"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func tableFixture(schema string, stride int, keys ...uint32) []byte {
	b := make([]byte, 72+stride*len(keys))
	sig, _ := hex.DecodeString(schema)
	copy(b, sig)
	le.PutUint64(b[24:], uint64(len(b)-32))
	le.PutUint64(b[32:], 24)
	le.PutUint64(b[40:], uint64(len(keys)))
	le.PutUint64(b[48:], 1)
	le.PutUint64(b[56:], 40)
	le.PutUint64(b[64:], uint64(len(keys)))
	for i, k := range keys {
		le.PutUint64(b[72+i*stride:], uint64(k))
	}
	return b
}
func TestTypesCollisionAndPublished(t *testing.T) {
	b := tableFixture(typesSchema, 144, 10, 11, 12)
	for i, k := range []uint32{10, 11, 12} {
		p := 80 + i*144
		le.PutUint32(b[p+112:], k)
		le.PutUint32(b[p+116:], 100+k)
		le.PutUint32(b[p+132:], 1<<13)
		b[p+129] = 1
	}
	b[80+144+129] = 0
	le.PutUint32(b[80+288+132:], 0) // A true byte without its presence bit is not published.
	got, n, e := readTypes(b)
	if e != nil || n != 3 || len(got) != 1 || got[0].ID != 10 || got[0].NameID != 110 {
		t.Fatalf("%+v %d %v", got, n, e)
	}
	b[80+112] = 99
	if _, _, e = readTypes(b); e == nil {
		t.Fatal("accepted mismatched ID")
	}
}
func TestClassificationLayouts(t *testing.T) {
	b := tableFixture(groupsSchema, 32, 25, 26)
	for i, id := range []uint32{25, 26} {
		p := 72 + i*32
		le.PutUint32(b[p+4:], 6)
		le.PutUint32(b[p+8:], id)
		le.PutUint32(b[p+12:], 100+id)
	}
	groups, err := readGroups(b)
	if err != nil || groups[25] != (groupRecord{ID: 25, CategoryID: 6, NameID: 125}) || groups[26].NameID != 126 {
		t.Fatalf("groups: %+v %v", groups, err)
	}
	b[72+8]++
	if _, err := readGroups(b); err == nil {
		t.Fatal("accepted mismatched group ID")
	}
	c := tableFixture(categoriesSchema, 40, 6)
	le.PutUint32(c[80+8:], 6)
	le.PutUint32(c[80+12:], 400)
	categories, err := readCategories(c)
	if err != nil || categories[6].NameID != 400 {
		t.Fatalf("categories: %+v %v", categories, err)
	}
	c[80+8]++
	if _, err := readCategories(c); err == nil {
		t.Fatal("accepted mismatched category ID")
	}
}

func TestTypesFields(t *testing.T) {
	b := tableFixture(typesSchema, 144, 42)
	v := b[80:]
	le.PutUint64(v[0:], 0x4024000000000000)  // 10
	le.PutUint64(v[8:], 0x4034000000000000)  // 20
	le.PutUint64(v[16:], 0x403e000000000000) // 30
	le.PutUint64(v[56:], 0x4044000000000000) // 40
	le.PutUint32(v[24:], 2)
	le.PutUint32(v[64:], 88)
	le.PutUint32(v[80:], 25)
	le.PutUint32(v[88:], 17)
	le.PutUint32(v[112:], 42)
	le.PutUint32(v[132:], 1<<13|1<<2|1<<7)
	v[129] = 1
	got, _, err := readTypes(b)
	if err != nil || len(got) != 1 {
		t.Fatalf("%v %v", got, err)
	}
	x := got[0]
	if x.BasePrice != 10 || x.Capacity != 20 || x.Mass != 30 || x.Volume != 40 || x.PortionSize != 2 || x.DescriptionID != 88 || x.GroupID != 25 || x.MarketGroupID == nil || *x.MarketGroupID != 17 {
		t.Fatalf("%+v", x)
	}
	le.PutUint64(v[0:], 0x7ff0000000000000)
	if _, _, err = readTypes(b); err == nil {
		t.Fatal("accepted infinity")
	}
}

func TestDatabase(t *testing.T) {
	p := filepath.Join(t.TempDir(), "static_data.db")
	desc := "=Not a formula"
	items := []item{{ID: 42, Name: "Ship", NameID: 100, DescriptionID: 101, Description: &desc, GroupID: 25, Published: true, Mass: 12.5, Volume: 7, Capacity: 0, PortionSize: 1, Status: "missing"}}
	groups := map[uint32]groupRecord{25: {ID: 25, CategoryID: 6, NameID: 125}}
	categories := map[uint32]categoryRecord{6: {ID: 6, NameID: 106}}
	if err := writeDatabase(p, items, groups, categories, map[uint32]string{125: "Frigate", 106: "Ship"}); err != nil {
		t.Fatal(err)
	}
	db, err := sql.Open("sqlite", p)
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	var name, description, group, category string
	var mass float64
	var market, icon sql.NullInt64
	if err := db.QueryRow(`SELECT typeName,description,groupName,categoryName,mass,marketGroupId,iconId FROM Types JOIN Groups USING(groupId) JOIN Categories USING(categoryId) WHERE typeId=42`).Scan(&name, &description, &group, &category, &mass, &market, &icon); err != nil {
		t.Fatal(err)
	}
	if name != "Ship" || description != desc || group != "Frigate" || category != "Ship" || mass != 12.5 || market.Valid || icon.Valid {
		t.Fatal(name, description, group, category, mass, market, icon)
	}
	var integrity string
	if err := db.QueryRow("PRAGMA integrity_check").Scan(&integrity); err != nil || integrity != "ok" {
		t.Fatalf("%s %v", integrity, err)
	}
}

func TestFSDBounds(t *testing.T) {
	for _, change := range []func([]byte){func(b []byte) { b[0] ^= 1 }, func(b []byte) { le.PutUint64(b[56:], ^uint64(0)) }, func(b []byte) { le.PutUint64(b[64:], 100000) }, func(b []byte) { le.PutUint64(b[40:], 5) }} {
		b := tableFixture(typesSchema, 144, 1)
		change(b)
		if _, e := fsdEntries(b, typesSchema, 144); e == nil {
			t.Fatal("accepted malformed table")
		}
	}
	b := tableFixture(typesSchema, 144, 1, 1)
	if _, e := fsdEntries(b, typesSchema, 144); e == nil {
		t.Fatal("accepted duplicate key")
	}
}
func TestIconFilePresenceOffset(t *testing.T) {
	b := tableFixture(iconsSchema, 32, 7)
	b = append(b, make([]byte, 8)...)
	length := len(b)
	b = append(b, []byte("res:/icon.png")...)
	le.PutUint64(b[length-8:], uint64(len("res:/icon.png")))
	le.PutUint64(b[80:], uint64(length-32))
	le.PutUint32(b[100:], 1)
	le.PutUint64(b[24:], uint64(len(b)-32))
	icons, e := readIcons(b)
	if e != nil || icons[7] != "res:/icon.png" {
		t.Fatalf("%v %v", icons, e)
	}
}
func pickleFixture() []byte {
	// ('en-us', {42: ('Item', None, {})}) with memo references for text.
	return []byte{0x80, 4, 0x8c, 5, 'e', 'n', '-', 'u', 's', 0x94, '}', 0x94, 'K', 42, 0x8c, 4, 'I', 't', 'e', 'm', 0x94, 'N', '}', 0x87, 0x94, 's', 0x86, '.'}
}
func TestLocalization(t *testing.T) {
	b := pickleFixture()
	got, e := localization(b)
	if e != nil || got[42] != "Item" {
		t.Fatalf("%v %v", got, e)
	}
	for i := 0; i < len(b); i++ {
		if _, e := localization(b[:i]); e == nil {
			t.Fatalf("accepted truncation %d", i)
		}
	}
	for _, op := range []byte{'c', 0x93, 'R', 'b', 'P', 'Q'} {
		if _, e := localization([]byte{0x80, 4, op, '.'}); e == nil {
			t.Fatalf("accepted executable opcode %x", op)
		}
	}
	if _, e := localization([]byte{0x80, 4, 'h', 99, '.'}); e == nil {
		t.Fatal("accepted invalid memo")
	}
	// Non-comparable tuple in root language position must return an error, not panic.
	if _, e := localization([]byte{0x80, 4, 'N', 'N', 0x86, '}', 0x86, '.'}); e == nil {
		t.Fatal("accepted invalid root")
	}
}
func TestIconFamilies(t *testing.T) {
	if iconFamily("res:/icons/123_64.png") != iconFamily("res:/icons/123_512.jpg") {
		t.Fatal("resolution variants did not match")
	}
	if iconFamily("res:/icons/7_64_1.png") == iconFamily("res:/icons/7_64_2.png") {
		t.Fatal("different icons merged")
	}
}
func TestIndexValidation(t *testing.T) {
	good := "res:/x,aa/aaaaaaaaaaaaaaaa_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,4,3\n"
	if _, e := parseIndex([]byte(good)); e != nil {
		t.Fatal(e)
	}
	for _, b := range []string{strings.Replace(good, "aa/aaaaaaaaaaaaaaaa_", "../aaaaaaaaaaaaaaaa_", 1), strings.Replace(good, ",4,", ",-4,", 1), good + strings.Replace(good, ",4,", ",5,", 1)} {
		if _, e := parseIndex([]byte(b)); e == nil {
			t.Fatal("accepted malformed index")
		}
	}
}
func TestOutputSafety(t *testing.T) {
	root := t.TempDir()
	if _, e := outputPath(root, filepath.Join(root, "out")); e == nil {
		t.Fatal("accepted output inside source")
	}
	if _, e := outputPath(root, root); e == nil {
		t.Fatal("accepted output equal to source")
	}
	outside := t.TempDir()
	if _, e := outputPath(root, filepath.Join(outside, "new")); e != nil {
		t.Fatal(e)
	}
	link := filepath.Join(outside, "alias")
	if e := os.Symlink(root, link); e == nil {
		if _, e := outputPath(root, filepath.Join(link, "out")); e == nil {
			t.Fatal("accepted symlink escape")
		}
	}
	if e := extract(root, outside); e == nil {
		t.Fatal("accepted existing output")
	}
}
func TestCSV(t *testing.T) {
	p := filepath.Join(t.TempDir(), "items.csv")
	desc := "+cmd"
	if e := writeCSV(p, []item{{ID: 42, Name: "=SUM(1,2)", Description: &desc, Status: "missing"}}); e != nil {
		t.Fatal(e)
	}
	b, _ := os.ReadFile(p)
	rows, e := csv.NewReader(bytes.NewReader(b)).ReadAll()
	if e != nil || rows[1][1] != "'=SUM(1,2)" || rows[1][13] != "'+cmd" {
		t.Fatalf("%v %v", rows, e)
	}
}
func TestDDSDimensions(t *testing.T) {
	b := make([]byte, 128)
	copy(b, "DDS ")
	le.PutUint32(b[4:], 124)
	le.PutUint32(b[76:], 32)
	le.PutUint32(b[12:], 512)
	le.PutUint32(b[16:], 1024)
	w, h, e := ddsDimensions(b)
	if e != nil || w != 1024 || h != 512 {
		t.Fatalf("%d %d %v", w, h, e)
	}
	if _, _, e := ddsDimensions(b[:40]); e == nil {
		t.Fatal("accepted truncated DDS")
	}
}
func FuzzLocalization(f *testing.F) {
	f.Add(pickleFixture())
	f.Add([]byte{0x80, 4, 'R'})
	f.Fuzz(func(t *testing.T, b []byte) {
		if len(b) > 1<<20 {
			t.Skip()
		}
		_, _ = localization(b)
	})
}
func FuzzFSD(f *testing.F) {
	f.Add(tableFixture(typesSchema, 144, 1))
	f.Fuzz(func(t *testing.T, b []byte) { _, _, _ = readTypes(b) })
}

// Opt-in real-installation test: no proprietary fixtures are checked into source.
func TestInstalledGame(t *testing.T) {
	root := os.Getenv("FRONTIER_GAME_TEST")
	if root == "" {
		t.Skip("set FRONTIER_GAME_TEST to opt in")
	}
	before := map[string][32]byte{}
	for _, n := range []string{"index_stillness.txt", "stillness/resfileindex.txt", "stillness/resfileindex_Windows.txt"} {
		b, e := os.ReadFile(filepath.Join(root, n))
		if e != nil {
			t.Fatal(e)
		}
		before[n] = sha256.Sum256(b)
	}
	out := filepath.Join(t.TempDir(), "export")
	if e := extract(root, out); e != nil {
		t.Fatal(e)
	}
	for n, want := range before {
		b, e := os.ReadFile(filepath.Join(root, n))
		if e != nil || sha256.Sum256(b) != want {
			t.Fatalf("source index changed: %s", n)
		}
	}
	b, e := os.ReadFile(filepath.Join(out, "items.json"))
	if e != nil {
		t.Fatal(e)
	}
	var items []item
	if e = json.Unmarshal(b, &items); e != nil {
		t.Fatal(e)
	}
	if len(items) == 0 {
		t.Fatal("no published types")
	}
	db, e := sql.Open("sqlite", filepath.Join(out, "static_data.db"))
	if e != nil {
		t.Fatal(e)
	}
	defer db.Close()
	var count int
	if e = db.QueryRow("SELECT count(*) FROM Types").Scan(&count); e != nil || count != len(items) {
		t.Fatalf("database type count %d: %v", count, e)
	}
	for _, it := range items {
		var name string
		var mass float64
		var groupID uint32
		if e = db.QueryRow("SELECT typeName, mass, groupId FROM Types WHERE typeId=?", it.ID).Scan(&name, &mass, &groupID); e != nil || name != it.Name || mass != it.Mass || groupID != it.GroupID {
			t.Fatalf("database mismatch for %d: %v", it.ID, e)
		}
	}
	g, e := openGame(root)
	if e != nil {
		t.Fatal(e)
	}
	defer g.root.Close()
	icons := 0
	for i, it := range items {
		if !it.Published || it.Name == "" || (i > 0 && items[i-1].ID >= it.ID) {
			t.Fatalf("invalid item %+v", it)
		}
		if it.Status == "available" {
			icons++
			b, e := os.ReadFile(filepath.Join(out, filepath.FromSlash(it.Icon)))
			if e != nil {
				t.Fatal(e)
			}
			original, e := g.get(it.IconResource)
			if e != nil || !bytes.Equal(b, original) {
				t.Fatalf("icon changed: %d", it.ID)
			}
		}
	}
	if icons == 0 {
		t.Fatal("no icons")
	}
	t.Logf("verified %d sorted published items and %d byte-identical icons; source index hashes unchanged", len(items), icons)
}
