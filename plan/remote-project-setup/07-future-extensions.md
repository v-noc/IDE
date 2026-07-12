# 7 — Future extensions (after MVP)

These are intentionally **out of scope** for the first slice but compatible with the design above.

1. **Persist remote metadata on `ProjectSchema`**  
   Fields: `remote_url`, `remote_db_id`, `last_pushed_commit`, etc. Enables UI to show sync state without re-entering URL.

2. **Encrypted or server-stored credentials**  
   Only if product requires; increases compliance and attack surface.

3. **Named remotes CRUD**  
   REST wrappers around Terminus remote management with per-environment URLs.

4. **Automatic pull on watcher / schedule**  
   Background jobs with stored read-only tokens.

5. **Conflict policy**  
   Document merge behavior when local and remote diverge; Terminus versioning semantics.

6. **Saga / rollback**  
   Compensating transactions when meta insert fails after `clonedb` or remote bootstrap.

7. **Shared `bootstrap_empty_project_db` tests**  
   Golden-path tests against Terminus test container for both local-only and remote-first.
