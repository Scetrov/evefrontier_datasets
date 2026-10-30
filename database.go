package main

import (
	"database/sql"
	"fmt"
	"sort"

	_ "modernc.org/sqlite"
)

// writeDatabase writes only client base data; it does not calculate fitted stats.
func writeDatabase(path string, items []item, groups map[uint32]groupRecord, categories map[uint32]categoryRecord, names map[uint32]string) (err error) {
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return err
	}
	defer func() {
		if closeErr := db.Close(); err == nil {
			err = closeErr
		}
	}()
	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	_, err = tx.Exec(`
PRAGMA user_version = 1;
CREATE TABLE Categories (categoryId INTEGER PRIMARY KEY, categoryName TEXT, nameId INTEGER NOT NULL);
CREATE TABLE Groups (groupId INTEGER PRIMARY KEY, groupName TEXT, nameId INTEGER NOT NULL, categoryId INTEGER);
CREATE TABLE Types (
 typeId INTEGER PRIMARY KEY, typeName TEXT NOT NULL, nameId INTEGER NOT NULL,
 description TEXT, descriptionId INTEGER, groupId INTEGER NOT NULL,
 published INTEGER NOT NULL, mass REAL NOT NULL, volume REAL NOT NULL,
 capacity REAL NOT NULL, portionSize INTEGER NOT NULL, basePrice REAL NOT NULL,
 marketGroupId INTEGER, iconId INTEGER, graphicId INTEGER,
 icon TEXT, iconResource TEXT, iconWidth INTEGER NOT NULL, iconHeight INTEGER NOT NULL,
 iconStatus TEXT NOT NULL
);
CREATE INDEX types_group_id ON Types(groupId);
CREATE INDEX groups_category_id ON Groups(categoryId);`)
	if err != nil {
		return fmt.Errorf("create database schema: %w", err)
	}
	name := func(id uint32) any {
		if s, ok := names[id]; ok {
			return s
		}
		return nil
	}
	categoryIDs := make([]int, 0, len(categories))
	for id := range categories {
		categoryIDs = append(categoryIDs, int(id))
	}
	sort.Ints(categoryIDs)
	for _, id := range categoryIDs {
		c := categories[uint32(id)]
		if _, err = tx.Exec("INSERT INTO Categories VALUES (?, ?, ?)", c.ID, name(c.NameID), c.NameID); err != nil {
			return err
		}
	}
	groupIDs := make([]int, 0, len(groups))
	for id := range groups {
		groupIDs = append(groupIDs, int(id))
	}
	sort.Ints(groupIDs)
	for _, id := range groupIDs {
		g := groups[uint32(id)]
		if _, err = tx.Exec("INSERT INTO Groups VALUES (?, ?, ?, ?)", g.ID, name(g.NameID), g.NameID, g.CategoryID); err != nil {
			return err
		}
	}
	stmt, err := tx.Prepare("INSERT INTO Types VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
	if err != nil {
		return err
	}
	defer stmt.Close()
	optionalID := func(id uint32) any {
		if id == 0 {
			return nil
		}
		return id
	}
	optionalText := func(s string) any {
		if s == "" {
			return nil
		}
		return s
	}
	for _, it := range items {
		_, err = stmt.Exec(it.ID, it.Name, it.NameID, it.Description, optionalID(it.DescriptionID), it.GroupID,
			it.Published, it.Mass, it.Volume, it.Capacity, it.PortionSize, it.BasePrice,
			it.MarketGroupID, optionalID(it.IconID), optionalID(it.GraphicID), optionalText(it.Icon), optionalText(it.IconResource),
			it.Width, it.Height, it.Status)
		if err != nil {
			return fmt.Errorf("insert type %d: %w", it.ID, err)
		}
	}
	if err = stmt.Close(); err != nil {
		return err
	}
	return tx.Commit()
}
