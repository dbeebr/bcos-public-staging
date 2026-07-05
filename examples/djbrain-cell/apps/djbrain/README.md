# djbrain App Package

`djbrain` is an example of an active BCOS app package.

Use this package for the domain-specific material that belongs to djbrain itself.

## Local folders

```text
knowledge/
prompts/
reports/
proofs/
```

## Routing

- Put stable source context in `knowledge/`.
- Put reusable prompt payloads in `prompts/`.
- Put app-specific analysis in `reports/`.
- Put app-specific evidence in `proofs/`.

When something becomes useful beyond djbrain, distill it into the Cell-level `library/`.
