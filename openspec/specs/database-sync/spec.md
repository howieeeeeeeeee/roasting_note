
### Requirement: Online-to-Local Sync
The user can pull data from MongoDB Atlas into their local database.

#### Scenario: Online-to-local sync runs
- **WHEN** POST `/api/sync/online-to-local` is called
- **THEN** all non-archived beans and roasts from Atlas are synced into the local database
- **AND** new documents are inserted
- **AND** existing documents (matched by `_id`) are updated with the latest online version
- **AND** the response includes counts: `beans_added`, `beans_updated`, `roasts_added`, `roasts_updated`

#### Scenario: Archived documents excluded
- **WHEN** a document in Atlas has `archived: true`
- **THEN** it is excluded from the sync and not inserted or updated locally

---

### Requirement: Local-to-Online Sync
The user can push local data to MongoDB Atlas.

#### Scenario: Local-to-online sync runs
- **WHEN** POST `/api/sync/local-to-online` is called
- **THEN** all non-archived local beans and roasts are synced to Atlas
- **AND** new documents are inserted
- **AND** existing documents in Atlas are updated with the local version
- **AND** the response includes counts: `beans_added`, `beans_updated`, `roasts_added`, `roasts_updated`

<!-- Database mode switching is covered in settings-configuration spec -->
