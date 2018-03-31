# faas-form

A command line tool invoking self-describing Lambda functions.

## Creation

A `faas-form`-compatible Lambda function is one that can report a simple schema for its input. When invoked with an event of the form:

```
{
  "x-faas-form-request": "schema"
}
```

This can be tested for in the handler with the `faas_form.is_schema_request(event)` function.

The Lambda must return an object that looks like:

```
{
  "x-faas-form-schema": {
    "instructions": <optional description to print before user input>,
    "inputs": [
      ...
    ]
  }
}
```

Each input corresponds to a field in the event object that the Lambda expects. Each input has a name, corresponding to the field name, a input type, and an optional help field to display when prompting the user for a value.

The client then prompts the user for values for the inputs, assembles them into an object and invokes the Lambda, including the field `"x-faas-form-request": "invoke"` in the request. This can be tested for in the handler with the `faas_form.is_invoke_request(event)` function.

### String inputs
```
{
  "type": "string",
  "name": <input name>,
  "pattern": <optional regex>,
  "help": <optional help>,
  "default": <optional default value>
}
```
The default value, if given, will be used when the user inputs an empty string.

### Secret inputs
```
{
  "type": "secret",
  "name": <input name>,
  "pattern": <optional regex>,
  "help": <optional help>
}
```
Like the string input, but will not echo when prompting the user, and does not accept a default.

### Number inputs
```
{
  "type": "number",
  "name": <input name>,
  "help": <optional help>,
  "default": <optional default value>
}
```

### Tagging

`faas-form`-compatible Lambdas can be made discoverable through two mechanisms: a resource tag on the Lambda or an entry in the Lambda's environment variables. In either case, the key must be `faasform` and the value is an optional short description. The environment variable form is available for situations where tagging is not desired.

## Usage

### Discovery

```bash
faas-form ls [--tags] [--env]
```

Lists the available `faas-form`-compatible Lambdas and their descriptions (if any). This will check for both tags and environment variables, unless one of the `--tags` or `--env` flags are set.

### Invocation

```bash
faas-form invoke FUNCTION_NAME
```

Request the schema from the given function, prompt for the inputs, invoke the function, and print the response.

### Admin

```bash
faas-form admin add FUNCTION_NAME [--description DESCRIPTION]
```

Tag the given function as a `faas-form`-compatible Lambda, optionally with a short description.


```bash
faas-form admin rm FUNCTION_NAME
```

Remove the tag marking the given function as a `faas-form`-compatible Lambda. Note this does not work with Lambdas marked using environment variables.
