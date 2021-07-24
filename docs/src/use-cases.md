--8<-- "refs.md"

# Use Cases

## Default syntax for new files

Sometimes, mostly in a project, you just want to have this functionality.

For example, you may want a new file[^1] to be auto set to
`JavaScript`, `React` or `Vue` syntax in a frontend web project.

!!! info

    Check the `new_file_syntax` plugin setting.

## Detecting the syntax when modifying the file

This method works only under following circumstances:

- The view's syntax is currently `Plain Text`.
- And the user is modifying either the first line or the last few chars of the file.

A typical use case is that if you create a new file and type `<?php`, the file will automatically
be set to `PHP` syntax because the `PHP` syntax claims it handles files whose first line is `<?php`.

!!! tip

    This also works with user-defined rule so when you copy and paste codes from
    a random website into ST, your defined rule may help you set the syntax too, because you are
    very likely modifying either the first line or the last few characters.

## Trimming unimportant suffixes from the filename

When a file is loaded, this plugin deduces the syntax for your "`Plain Text`" file by its filename.

For example, you may have a configuration file whose name is `parameters.yml.dist`.
ST can't find a syntax for a `.dist` extension so your `parameters.yml.dist` remains `Plain Text`.

However, this plugin will try to remove unimportant suffixes from the filename.
By default, `.dist` is in the `trim_suffixes` list, so this plugin will remove it and try whether
it can find a syntax for `parameters.yml`, and yes, it deserves the `YAML` syntax.

!!! info

    Check `default_trim_suffixes`, `user_trim_suffixes` and `project_trim_suffixes` plugin settings.

## Assigning syntax by the first line

If a file has a characteristic first line, this plugin prefers the syntax set by it whenever possible.

Wait... wouldn't this already be done by ST itself? Yes, but there are some corner cases.
For example, say you have a file whose name is "[rdm.ts]" but it's actually a `XML` file.
ST will set the syntax to unwanted `TypeScript`, because its extension `ts`
is in the `file_extensions` of the `TypeScript` syntax.

!!! info

    ST prefers assigning the syntax basing on the file name (extension) than the first line.
    Probably because it doesn't have to actually read the file,
    although the first line may provide more precise information.

## User-defined rules

- For average users, read "[Configurations][plugin-configurations]" for more details to create your own rules.
- For advanced users, you may read "Advanced Topics" for creating custom `Match` or `Constraint` implementations.

[rdm.ts]: https://github.com/uglide/RedisDesktopManager/blob/783540ab/src/resources/translations/rdm.ts

[^1]: Create a new file: ++ctrl+n++ for Windows/Linux. ++cmd+n++ for macOS.