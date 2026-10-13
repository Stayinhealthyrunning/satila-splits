# Sätila source archive – privacy and retention notice

**2026-10-13 security correction:** A former workflow stored a complete 422-file EQ Timing reconstruction archive as a ZIP in this **public** GitHub repository. Keeping it outside `docs/` excluded it from GitHub Pages, but **did not make it private**.

The source ZIP and its public republishing workflow have been removed from the current branch. This is a **current-tree exposure reduction only**: prior Git commits, forks, GitHub caches, and previously downloaded copies may still contain the file. Do not describe the archive as fully deleted or the incident as closed.

The original temporary GitHub Actions artifact is `satila-eqtiming-raw-36818159977` (run `36818159977`, artifact ID `11142571759`, expiry `2026-10-31T05:09:48Z`). Issue [#6](https://github.com/Stayinhealthyrunning/satila-splits/issues/6) tracks preservation to a **private, access-controlled** storage location, encrypted backup and restoration verification, ideally before October 25. Do **not** recommit the raw archive, source contestant JSON, network/browser traces or other original personal records to a public repo.

A later history purge or external-cache takedown needs a verified private backup and coordinated admin review first. Force-rewriting public Git history may invalidate clones, tags and release references and is **not** performed in this correction.

The existing participant GPX/source package in this directory is separate and requires an independent provenance, redistribution-rights and privacy review. The sanitized `docs/data/` files remain the only intended publicly served race results.
