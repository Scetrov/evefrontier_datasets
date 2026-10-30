package main

import (
	"bytes"
	"encoding/csv"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"image"
	_ "image/jpeg"
	_ "image/png"
	"os"
	"path"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

type item struct {
	ID            uint32   `json:"id"`
	Name          string   `json:"name"`
	NameID        uint32   `json:"name_id"`
	DescriptionID uint32   `json:"description_id"`
	Description   *string  `json:"description"`
	GroupID       uint32   `json:"group_id"`
	GroupName     *string  `json:"group_name"`
	CategoryID    *uint32  `json:"category_id"`
	CategoryName  *string  `json:"category_name"`
	MarketGroupID *uint32  `json:"market_group_id"`
	Mass          float64  `json:"mass"`
	Volume        float64  `json:"volume"`
	Capacity      float64  `json:"capacity"`
	PortionSize   uint32   `json:"portion_size"`
	BasePrice     float64  `json:"base_price"`
	IconID        uint32   `json:"icon_id"`
	GraphicID     uint32   `json:"graphic_id"`
	Published     bool     `json:"published"`
	Icon          string   `json:"icon"`
	IconResource  string   `json:"icon_resource"`
	Width         int      `json:"width"`
	Height        int      `json:"height"`
	Status        string   `json:"icon_status"`
	Issues        []string `json:"issues,omitempty"`
}
type report struct {
	TotalTypes          int               `json:"total_types"`
	Published           int               `json:"published_types"`
	Icons               int               `json:"icons_exported"`
	Missing             int               `json:"icons_missing"`
	AtLeast512          int               `json:"icons_at_least_512px"`
	MissingNames        int               `json:"missing_names"`
	MissingDescriptions int               `json:"missing_descriptions"`
	MissingGroups       int               `json:"missing_groups"`
	MissingCategories   int               `json:"missing_categories"`
	SourceHashes        map[string]string `json:"source_md5"`
}
type imageAsset struct {
	r    resource
	data []byte
	w, h int
	err  error
}

func main() {
	gameDir := flag.String("game", `C:\CCP\EVE Frontier`, "game cache root (read-only)")
	out := flag.String("out", "frontier-items", "NEW output directory, outside game root")
	flag.Parse()
	if flag.NArg() != 0 {
		fmt.Fprintln(os.Stderr, "unexpected positional arguments")
		os.Exit(2)
	}
	if e := extract(*gameDir, *out); e != nil {
		fmt.Fprintln(os.Stderr, "extract:", e)
		os.Exit(1)
	}
}

func outputPath(gameDir, out string) (string, error) {
	source, e := filepath.EvalSymlinks(gameDir)
	if e != nil {
		return "", e
	}
	source, e = filepath.Abs(source)
	if e != nil {
		return "", e
	}
	dest, e := filepath.Abs(out)
	if e != nil {
		return "", e
	}
	// Require an existing parent so aliases/junctions can be resolved before writing.
	parent, e := filepath.EvalSymlinks(filepath.Dir(dest))
	if e != nil {
		return "", fmt.Errorf("output parent must exist: %w", e)
	}
	dest = filepath.Join(parent, filepath.Base(dest))
	rel, e := filepath.Rel(strings.ToLower(source), strings.ToLower(dest))
	if e != nil {
		return "", e
	}
	if rel == "." || (rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator))) {
		return "", fmt.Errorf("output must be outside game directory")
	}
	return dest, nil
}

func extract(gameDir, out string) error {
	dest, e := outputPath(gameDir, out)
	if e != nil {
		return e
	}
	// Refuse overwrites, including symlinks to an existing destination.
	if _, e := os.Lstat(dest); !errors.Is(e, os.ErrNotExist) {
		return fmt.Errorf("output must not already exist: %s", dest)
	}
	g, e := openGame(gameDir)
	if e != nil {
		return e
	}
	defer g.root.Close()
	b, e := g.get("res:/staticdata/types.fsdbinary")
	if e != nil {
		return e
	}
	types, total, e := readTypes(b)
	if e != nil {
		return e
	}
	b, e = g.get("res:/staticdata/groups.fsdbinary")
	if e != nil {
		return e
	}
	groups, e := readGroups(b)
	if e != nil {
		return e
	}
	b, e = g.get("res:/staticdata/categories.fsdbinary")
	if e != nil {
		return e
	}
	categories, e := readCategories(b)
	if e != nil {
		return e
	}
	b, e = g.get("res:/staticdata/iconids.fsdbinary")
	if e != nil {
		return e
	}
	icons, e := readIcons(b)
	if e != nil {
		return e
	}
	b, e = g.get("res:/staticdata/graphicids.fsdbinary")
	if e != nil {
		return e
	}
	folders, e := readGraphicFolders(b)
	if e != nil {
		return e
	}
	b, e = g.get("res:/localizationfsd/localization_fsd_en-us.pickle")
	if e != nil {
		return e
	}
	names, e := localization(b)
	if e != nil {
		return e
	}
	sort.Slice(types, func(i, j int) bool { return types[i].ID < types[j].ID })
	families := make(map[string][]resource)
	for uri, r := range g.resources {
		switch path.Ext(uri) {
		case ".png", ".jpg", ".jpeg", ".dds":
			families[iconFamily(uri)] = append(families[iconFamily(uri)], r)
		}
	}
	for _, rs := range families {
		sort.Slice(rs, func(i, j int) bool { return rs[i].URI < rs[j].URI })
	}
	// Stage output outside the installation. Publish the completed directory once.
	stage, e := os.MkdirTemp(filepath.Dir(dest), ".frontier-extract-")
	if e != nil {
		return e
	}
	defer os.RemoveAll(stage)
	if e = os.Mkdir(filepath.Join(stage, "icons"), 0755); e != nil {
		return e
	}
	assets := make(map[string]*imageAsset)
	getAsset := func(r resource) *imageAsset {
		if a, ok := assets[r.URI]; ok {
			return a
		}
		a := &imageAsset{r: r}
		assets[r.URI] = a
		a.data, a.err = g.load(r)
		if a.err == nil {
			if path.Ext(r.URI) == ".dds" {
				a.w, a.h, a.err = ddsDimensions(a.data)
			} else {
				var c image.Config
				c, _, a.err = image.DecodeConfig(bytes.NewReader(a.data))
				a.w, a.h = c.Width, c.Height
			}
			if a.err == nil && (a.w <= 0 || a.h <= 0 || a.w > 32768 || a.h > 32768) {
				a.err = fmt.Errorf("invalid image dimensions")
			}
		}
		return a
	}
	var items []item
	summary := report{TotalTypes: total, Published: len(types), SourceHashes: g.reads}
	for _, t := range types {
		it := item{ID: t.ID, Name: names[t.NameID], NameID: t.NameID, DescriptionID: t.DescriptionID,
			GroupID: t.GroupID, MarketGroupID: t.MarketGroupID, Mass: t.Mass, Volume: t.Volume,
			Capacity: t.Capacity, BasePrice: t.BasePrice, PortionSize: t.PortionSize,
			IconID: t.IconID, GraphicID: t.GraphicID, Published: true, Status: "missing"}
		if t.DescriptionID != 0 {
			if value, ok := names[t.DescriptionID]; ok {
				it.Description = &value
			} else {
				it.Issues = append(it.Issues, "description_localization_missing")
			}
		}
		if group, ok := groups[t.GroupID]; ok {
			if value, ok := names[group.NameID]; ok {
				it.GroupName = &value
			} else {
				it.Issues = append(it.Issues, "group_localization_missing")
			}
			id := group.CategoryID
			it.CategoryID = &id
			if category, ok := categories[id]; ok {
				if value, ok := names[category.NameID]; ok {
					it.CategoryName = &value
				} else {
					it.Issues = append(it.Issues, "category_localization_missing")
				}
			} else {
				it.Issues = append(it.Issues, "category_missing")
			}
		} else {
			it.Issues = append(it.Issues, "group_missing")
		}
		if it.Description == nil {
			summary.MissingDescriptions++
		}
		if it.GroupName == nil {
			summary.MissingGroups++
		}
		if it.CategoryName == nil {
			summary.MissingCategories++
		}
		if it.Name == "" {
			summary.MissingNames++
			it.Issues = append(it.Issues, "localization_missing")
		}
		candidates := make(map[string]resource)
		addFamily := func(uri string) {
			if uri != "" {
				for _, r := range families[iconFamily(strings.ToLower(uri))] {
					candidates[r.URI] = r
				}
			}
		}
		if t.IconID != 0 {
			addFamily(icons[t.IconID])
		}
		if t.GraphicID != 0 {
			if folder := strings.TrimRight(strings.ToLower(folders[t.GraphicID]), "/"); folder != "" {
				addFamily(fmt.Sprintf("%s/%d_512.jpg", folder, t.GraphicID))
			}
		}
		uris := make([]string, 0, len(candidates))
		for uri := range candidates {
			uris = append(uris, uri)
		}
		sort.Strings(uris)
		var best *imageAsset
		for _, uri := range uris {
			a := getAsset(candidates[uri])
			if a.err != nil {
				it.Issues = append(it.Issues, uri+": "+a.err.Error())
				continue
			}
			if best == nil || int64(a.w)*int64(a.h) > int64(best.w)*int64(best.h) {
				best = a
			}
		}
		if best != nil {
			it.Width, it.Height = best.w, best.h
			it.IconResource = best.r.URI
			it.Icon = fmt.Sprintf("icons/%d%s", t.ID, path.Ext(best.r.URI))
			it.Status = "available"
			if e = os.WriteFile(filepath.Join(stage, filepath.FromSlash(it.Icon)), best.data, 0644); e != nil {
				return e
			}
			summary.Icons++
			if it.Width >= 512 && it.Height >= 512 {
				summary.AtLeast512++
			}
		} else {
			summary.Missing++
		}
		items = append(items, it)
	}
	if e = writeDatabase(filepath.Join(stage, "static_data.db"), items, groups, categories, names); e != nil {
		return e
	}
	if e = writeJSON(filepath.Join(stage, "items.json"), items); e != nil {
		return e
	}
	if e = writeJSON(filepath.Join(stage, "report.json"), summary); e != nil {
		return e
	}
	if e = writeCSV(filepath.Join(stage, "items.csv"), items); e != nil {
		return e
	}
	if _, e = os.Lstat(dest); !errors.Is(e, os.ErrNotExist) {
		return fmt.Errorf("output appeared during extraction; refusing overwrite")
	}
	if e = os.Rename(stage, dest); e != nil {
		return e
	}
	fmt.Printf("Exported %d published items: %d icons (%d at least 512px), %d missing icons, %d missing names.\nOutput: %s\n", summary.Published, summary.Icons, summary.AtLeast512, summary.Missing, summary.MissingNames, dest)
	return nil
}

func ddsDimensions(b []byte) (int, int, error) {
	if len(b) < 128 || string(b[:4]) != "DDS " || le.Uint32(b[4:]) != 124 || le.Uint32(b[76:]) != 32 {
		return 0, 0, fmt.Errorf("invalid DDS header")
	}
	return int(le.Uint32(b[16:])), int(le.Uint32(b[12:])), nil
}
func writeJSON(p string, v any) error {
	b, e := json.MarshalIndent(v, "", "  ")
	if e != nil {
		return e
	}
	return os.WriteFile(p, append(b, '\n'), 0644)
}
func spreadsheetText(s string) string {
	trimmed := strings.TrimLeft(s, " \t\r\n")
	if trimmed != "" && strings.ContainsRune("=+-@", rune(trimmed[0])) {
		return "'" + s
	}
	if strings.ContainsAny(s, "\t\r") {
		return "'" + s
	}
	return s
}
func csvText(s *string) string {
	if s == nil {
		return ""
	}
	return spreadsheetText(*s)
}
func csvID(id *uint32) string {
	if id == nil {
		return ""
	}
	return strconv.FormatUint(uint64(*id), 10)
}
func writeCSV(p string, items []item) error {
	f, e := os.Create(p)
	if e != nil {
		return e
	}
	w := csv.NewWriter(f)
	e = w.Write([]string{"id", "name", "name_id", "icon_id", "graphic_id", "published", "icon", "icon_resource", "width", "height", "icon_status", "issues", "description_id", "description", "group_id", "group_name", "category_id", "category_name", "market_group_id", "mass", "volume", "capacity", "portion_size", "base_price"})
	for _, it := range items {
		if e != nil {
			break
		}
		e = w.Write([]string{strconv.FormatUint(uint64(it.ID), 10), spreadsheetText(it.Name), strconv.FormatUint(uint64(it.NameID), 10), strconv.FormatUint(uint64(it.IconID), 10), strconv.FormatUint(uint64(it.GraphicID), 10), "true", it.Icon, it.IconResource, strconv.Itoa(it.Width), strconv.Itoa(it.Height), it.Status, spreadsheetText(strings.Join(it.Issues, "; ")),
			strconv.FormatUint(uint64(it.DescriptionID), 10), csvText(it.Description), strconv.FormatUint(uint64(it.GroupID), 10), csvText(it.GroupName), csvID(it.CategoryID), csvText(it.CategoryName), csvID(it.MarketGroupID), strconv.FormatFloat(it.Mass, 'g', -1, 64), strconv.FormatFloat(it.Volume, 'g', -1, 64), strconv.FormatFloat(it.Capacity, 'g', -1, 64), strconv.FormatUint(uint64(it.PortionSize), 10), strconv.FormatFloat(it.BasePrice, 'g', -1, 64)})
	}
	w.Flush()
	if e == nil {
		e = w.Error()
	}
	closeErr := f.Close()
	if e != nil {
		return e
	}
	return closeErr
}
