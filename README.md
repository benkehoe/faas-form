# faas-form

A command line tool invoking self-describing Lambda functions.
It is intended to help developers and administrators provide interfaces to Lambdas that are designed to be invoked directly by users.
This allows Lambda functions to replace client-side scripts for interactions with resources running on AWS.
It does not aim to support arbitrarily complex input schemas, but it does support multi-step workflows.

## Quickstart
```

$ git clone https://github.com/benkehoe/faas-form.git faas-form
$ cd faas-form
$ pip install --user .

$ aws cloudformation package --s3-bucket YOUR-BUCKET-NAME --template-file example_template.yaml --output-template-file example_template_packaged.yaml

$ aws cloudformation deploy --template example_template_packaged.yaml --stack-name faas-form-example --capabilities CAPABILITY_IAM

$ faas-form ls
faas-form-example       an example faas-form compatible lambda function

$ faas-form invoke faas-form-example
Hello! Thanks for trying faas-form.
name [string] Enter your name. Try "Merlin" to see advanced features (required=True):
```

## Creation

See the `example_lambda.py` Lambda function handler (and correponding SAM template `example_template.yaml` to deploy it).

A `faas-form`-compatible Lambda function is one that can report a simple schema for its input. When invoked with an event of the form:

```
{
  "x-faas-form-payload": "schema"
}
```

This can be tested for in the handler with the `faas_form.is_schema_request(event)` function.

The Lambda must return an object that looks like:

```
{
  "x-faas-form-schema": {
    "schema_version": "2018-04-01",
    "instructions": <optional description to print before user input>,
    "inputs": [
      ...
    ]
  }
}
```

Each input corresponds to a field in the event object that the Lambda expects. Each input has a name, corresponding to the field name, a input type, and an optional help field to display when prompting the user for a value.

The client then prompts the user for values for the inputs, assembles them into an object and invokes the Lambda, including the field `"x-faas-form-payload": "invoke"` in the request.
This can be tested for in the handler with the `faas_form.is_invoke_request(event)` function.

The Lambda processes the event, and returns a result to the client. Normally, the client will print the result object, but if the Lambda wants to control this output, it can set the field `x-faas-form-result` in the result object, and this will be printed instead.
This can also be set using `faas_form.set_result(response)`.

### Multi-step workflows

After the first invocation, the Lambda can re-prompt the user for more input. In the result object it returns, it can set the field `"x-faas-form-payload": "reinvoke"` (or using `faas_form.set_reinvoke_response(response)`), and then must also include a schema (under `x-faas-form-schema`).
The client will prompt the user with the new schema, and invoke the Lambda with the data.
The `const` input type can be useful in the scenario for keeping state between requests or to track the steps in the process.

### Input types

#### String inputs
```
{
  "type": "string",
  "name": <input name>,
  "pattern": <optional regex>,
  "help": <optional help>,
  "default": <optional default value>,
  "required": <boolean, default is true>
}
```
The default value, if given, will be used when the user inputs an empty string.

### Secret inputs
```
{
  "type": "secret",
  "name": <input name>,
  "pattern": <optional regex>,
  "help": <optional help>,
  "required": <boolean, default is true>
}
```
Like the string input, but will not echo when prompting the user, and does not accept a default.

### Number inputs
```
{
  "type": "number",
  "name": <input name>,
  "integer": <boolean indicating if integer values are required>,
  "help": <optional help>,
  "default": <optional default value>,
  "required": <boolean, default is true>
}
```

### Boolean inputs
```
{
  "type": "boolean",
  "name": <input name>,
  "help": <optional help>,
  "required": <boolean, default is true>
}
```

### String list inputs
```
{
  "type": "list<string>",
  "name": <input name>,
  "size": <optional fixed size>,
  "pattern": <optional regex for entries>,
  "help": <optional help>,
  "required": <boolean, default is true>
}
```

### Const inputs
```
{
  "type": "const",
  "value": <value>
}
```

## Tagging

`faas-form`-compatible Lambdas can be made discoverable through two mechanisms: a resource tag on the Lambda or an entry in the Lambda's environment variables.
In either case, the key must be `faasform` and the value is an optional short description.
The environment variable form is available for situations where tagging is not desired.

## Usage

### Discovery

```bash
faas-form ls [--tags/--no-tags] [--env/--no-env]
```

Lists the available `faas-form`-compatible Lambdas and their descriptions (if any).
By default, only checks tags. Use the flags to control whether it searches tags or environment variables.

### Invocation

```bash
faas-form invoke FUNCTION_NAME
```

Request the schema from the given function, prompt for the inputs, invoke the function, and print the response. Optionally, a schema can be provided with the `--schema` flag, which will cause the schema query step to be skipped.

### Development

```bash
faas-form prompt --schema SCHEMA [--output-file FILE]
```

Take the given schema, prompt for values, and print or store the resulting object. The schema object can have the top-level `x-faas-form-schema` key, or simply be the object that would be under that key.

```bash
faas-form prompt --function FUNCTION_NAME [--output-file FILE]
```

Query the given function for its schema, prompt for values, and print or store the resulting object.

### Admin

```bash
faas-form admin tag FUNCTION_NAME [--description DESCRIPTION]
```

Tag the given function as a `faas-form`-compatible Lambda, optionally with a short description.


```bash
faas-form admin untag FUNCTION_NAME
```

Remove the tag marking the given function as a `faas-form`-compatible Lambda. Note this does not work with Lambdas marked using environment variables.

```bash
faas-form admin show FUNCTION_NAME
```

Query the given function for its schema and print it.

## Status

Currently in a working state with Python 3. Tests for schema are done. Still to do:

* Tests for `faas` module
* Tests for `cli` module
* Ensure Python 2 compatibility
