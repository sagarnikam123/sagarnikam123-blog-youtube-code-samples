# Module 07 — Built-in Functions

## Overview

Terraform provides built-in functions organized into categories. You cannot define custom functions — only use the built-in ones.

**Tip:** Use `terraform console` to experiment with functions interactively!

```bash
$ terraform console
> upper("hello")
"HELLO"
> length([1, 2, 3])
3
> max(5, 12, 9)
12
```

## Function Categories

### String Functions
| Function | Example | Result |
|----------|---------|--------|
| `upper(s)` | `upper("hello")` | `"HELLO"` |
| `lower(s)` | `lower("HELLO")` | `"hello"` |
| `title(s)` | `title("hello world")` | `"Hello World"` |
| `trim(s, chars)` | `trim("  hi  ", " ")` | `"hi"` |
| `trimprefix(s, p)` | `trimprefix("helloworld", "hello")` | `"world"` |
| `trimsuffix(s, s)` | `trimsuffix("hello.txt", ".txt")` | `"hello"` |
| `replace(s, old, new)` | `replace("hello", "l", "L")` | `"heLLo"` |
| `split(sep, s)` | `split(",", "a,b,c")` | `["a","b","c"]` |
| `join(sep, list)` | `join("-", ["a","b"])` | `"a-b"` |
| `format(fmt, ...)` | `format("Hi %s, age %d", "Bob", 30)` | `"Hi Bob, age 30"` |
| `substr(s, off, len)` | `substr("hello", 0, 3)` | `"hel"` |
| `regex(pat, s)` | `regex("[a-z]+", "123abc")` | `"abc"` |
| `regexall(pat, s)` | `regexall("[0-9]+", "a1b2")` | `["1","2"]` |
| `startswith(s, p)` | `startswith("hello", "he")` | `true` |
| `endswith(s, s)` | `endswith("hello.tf", ".tf")` | `true` |

### Numeric Functions
| Function | Example | Result |
|----------|---------|--------|
| `abs(n)` | `abs(-5)` | `5` |
| `ceil(n)` | `ceil(4.2)` | `5` |
| `floor(n)` | `floor(4.8)` | `4` |
| `max(n...)` | `max(5, 12, 9)` | `12` |
| `min(n...)` | `min(5, 12, 9)` | `5` |
| `parseint(s, base)` | `parseint("FF", 16)` | `255` |
| `pow(base, exp)` | `pow(2, 8)` | `256` |

### Collection Functions
| Function | Example | Result |
|----------|---------|--------|
| `length(col)` | `length(["a","b"])` | `2` |
| `element(list, i)` | `element(["a","b","c"], 1)` | `"b"` |
| `index(list, val)` | `index(["a","b"], "b")` | `1` |
| `contains(list, v)` | `contains(["a","b"], "a")` | `true` |
| `concat(l1, l2)` | `concat(["a"], ["b"])` | `["a","b"]` |
| `flatten(list)` | `flatten([["a"],["b"]])` | `["a","b"]` |
| `distinct(list)` | `distinct(["a","a","b"])` | `["a","b"]` |
| `sort(list)` | `sort(["c","a","b"])` | `["a","b","c"]` |
| `reverse(list)` | `reverse(["a","b","c"])` | `["c","b","a"]` |
| `slice(list, s, e)` | `slice(["a","b","c"], 0, 2)` | `["a","b"]` |
| `compact(list)` | `compact(["a","","b"])` | `["a","b"]` |
| `keys(map)` | `keys({a=1, b=2})` | `["a","b"]` |
| `values(map)` | `values({a=1, b=2})` | `[1, 2]` |
| `lookup(map, k, def)` | `lookup({a=1}, "b", 0)` | `0` |
| `merge(m1, m2)` | `merge({a=1}, {b=2})` | `{a=1, b=2}` |
| `zipmap(k, v)` | `zipmap(["a","b"], [1,2])` | `{a=1, b=2}` |
| `one(list)` | `one(["single"])` | `"single"` |

### Encoding Functions
| Function | Description |
|----------|-------------|
| `jsonencode(val)` | Convert to JSON string |
| `jsondecode(str)` | Parse JSON string |
| `yamlencode(val)` | Convert to YAML string |
| `yamldecode(str)` | Parse YAML string |
| `base64encode(s)` | Base64 encode |
| `base64decode(s)` | Base64 decode |
| `csvdecode(str)` | Parse CSV string |
| `urlencode(s)` | URL-encode a string |

### Filesystem Functions
| Function | Description |
|----------|-------------|
| `file(path)` | Read file contents |
| `fileexists(path)` | Check if file exists |
| `templatefile(path, vars)` | Render a template file |
| `basename(path)` | Get filename from path |
| `dirname(path)` | Get directory from path |
| `pathexpand(path)` | Expand `~` in path |
| `abspath(path)` | Get absolute path |

### Type Conversion
| Function | Description |
|----------|-------------|
| `tostring(val)` | Convert to string |
| `tonumber(val)` | Convert to number |
| `tobool(val)` | Convert to bool |
| `tolist(val)` | Convert to list |
| `toset(val)` | Convert to set |
| `tomap(val)` | Convert to map |
| `try(expr, fallback)` | Return first non-error expression |
| `can(expr)` | Test if expression evaluates without error |
| `type(val)` | Return the type of a value |
| `nonsensitive(val)` | Remove sensitive marking |
| `sensitive(val)` | Mark a value as sensitive |

## Official Docs

- [Built-in Functions](https://developer.hashicorp.com/terraform/language/functions)
- [String Functions](https://developer.hashicorp.com/terraform/language/functions/upper)
- [Numeric Functions](https://developer.hashicorp.com/terraform/language/functions/max)
- [Collection Functions](https://developer.hashicorp.com/terraform/language/functions/length)
- [Encoding Functions](https://developer.hashicorp.com/terraform/language/functions/jsonencode)
- [Filesystem Functions](https://developer.hashicorp.com/terraform/language/functions/file)
- [Type Conversion Functions](https://developer.hashicorp.com/terraform/language/functions/tostring)
- [templatefile()](https://developer.hashicorp.com/terraform/language/functions/templatefile)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [String Functions](./01-string-functions/) | String manipulation in practice |
| 2 | [Collection Functions](./02-collection-functions/) | Lists, maps, and transformations |
| 3 | [Encoding & Filesystem](./03-encoding-filesystem/) | JSON, YAML, file(), templatefile() |
