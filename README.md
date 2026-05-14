# M3Undle CLI

`m3undle-cli` contains the `bndl` command-line adapter for M3Undle playlist and EPG workflows.

The CLI owns command parsing, terminal output, progress rendering, file output adapters, and exit-code mapping. Reusable playlist, provider, group, XMLTV, EPG, and classification behavior comes from the private `M3Undle.Core` NuGet package.

## Build

```bash
dotnet restore
dotnet build --configuration Release
dotnet test --configuration Release
```

## Core Package

`M3Undle.Core` is restored from the private Sydney-Elvis GitHub Packages feed. For local testing before a package is published, restore with a temporary NuGet config that maps `M3Undle.Core` to a local folder feed.

## Docs

- CLI usage: `docs/CLI.md`
- Command spec: `docs/spec/cli_spec.md`
- Groups file format: `docs/spec/groups_file_format.md`
- Environment placeholders: `docs/spec/env_usage.md`
