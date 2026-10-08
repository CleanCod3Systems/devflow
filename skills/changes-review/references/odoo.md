# Odoo checklist (17/18)

Apply only to the Odoo files touched. Findings follow the same rules as SKILL.md: anchored
on changed lines, with a concrete failure. On stable branches do not ask for restyling: the
existing file's style wins.

If the repo vendors Odoo's source (e.g. an `odoo/` or `<version>/` tree), check framework
signatures and behavior there before stating anything from memory. That tree is read-only:
a change inside it is always a mistake (extend it from your addons via inheritance).

## Models and ORM
- `_name`, `_inherit`, `_inherits` match the real domain; an `_inherit` does not
  accidentally replace a model that was meant to be extended.
- Batch operations: no `search()`, `browse()`, `create()`, `write()`, or `unlink()` inside
  loops without justification (N+1).
- Correct domains, indexed when filtered often, and safe in multi-company setups.
- `sudo()` only at explicit trust boundaries, with a comment explaining why, and never
  returning records the user should not see.
- Raw SQL always parameterized (`%s` with params, never f-strings or manual `%`).
- No business method calls `self.env.cr.commit()` unless the framework requires it.
- Errors that may abort the transaction are isolated with savepoints.

## Fields, computes, and constraints
- `@api.depends` lists every dependency, including dotted paths.
- `@api.constrains` uses real field names and raises `ValidationError`.
- `store=True` on computes is intentional; if the field is searched or grouped on, it must be stored.
- Monetary fields have their currency field; relational fields have the right `ondelete`.
- Deletion checks use `@api.ondelete`.

## Multi-company
- Models holding business data have `company_id`, `_check_company_auto = True`, and
  `check_company=True` on the relevant relational fields.
- Record rules per company for those models.
- Records from different companies are never mixed in one operation.

## Security
- Every new persistent model has its line in `ir.model.access.csv`.
- Realistic record rules for the groups and companies that use it.
- Public/portal controllers validate identity, ownership, `auth`, CSRF, and input.
- Sensitive fields have `groups=`; in QWeb, `t-esc`/`t-out` instead of `t-raw`.
- Odoo exceptions: `UserError`, `ValidationError`, `AccessError`.

## XML, views, and data
- View inheritance targets stable anchors (`xpath` by `name`, not by position).
- Actions, menus, reports, and crons reference XML IDs that exist.
- Manifest `data` order is load-safe: groups/security, ACLs, data, views, actions, menus.
- Reference data uses `noupdate` when it must not be overwritten on update.
- User-facing strings are translatable.

## Manifest, migrations, and deploy
- Manifest `depends` covers imports, inherited models, XML references, and assets.
- Schema changes (rename/drop a field, change a type or a `Selection`'s values) ship with an
  idempotent migration script (`migrations/<version>/pre-` or `post-migrate.py`).
- Lock risk on module upgrade (`-u`): a new stored computed field on a large table
  (recomputes everything), a new `required=True`, `index=True` without `CONCURRENTLY`, new
  `_sql_constraints`, type changes. If the table is large or its size unknown, it goes to
  🤔 / "Unverified".
- Renaming fields, events, or routes used by external integrations is a breaking change:
  search for usages outside the module before accepting it.

## Performance
- No N+1; aggregations with `_read_group`.
- Heavy or slow work runs outside the request (a job queue, e.g. OCA `queue_job` with `with_delay()`).

## OWL and assets
- JS/XML/SCSS files are in the right bundle.
- Components clean up listeners and async work when unmounted.

## Tests
- New logic, permissions, and migrations have tests (`TransactionCase` / `HttpCase`).
- Tests are isolated: they do not depend on order or leave side effects between runs.
