---
title: Run a Validation Definition
---
import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

import PrereqPythonInstalled from '../_core_components/prerequisites/_python_installation.md';
import PrereqGxInstalled from '../_core_components/prerequisites/_gx_installation.md';
import PrereqPreconfiguredDataContext from '../_core_components/prerequisites/_preconfigured_data_context.md';
import PrereqValidationDefinition from '../_core_components/prerequisites/_validation_definition.md';



<h2>Prerequisites</h2>

- <PrereqPythonInstalled/>.
- <PrereqGxInstalled/>.
- <PrereqPreconfiguredDataContext/>.
- <PrereqValidationDefinition/>.

<Tabs>

<TabItem value="procedure" label="Procedure">

1. Retrieve your Validation Definition.

   If you have created a new Validation Definition you can use the object returned by your Data Context's `.validation_definitions.add(...)` method.  Alternatively, you can retrieve a previously configured Validation Definition by updating the variable `validation_definition_name` in the following code and executing it:

   ```python title="Python
   import great_expectations as gx
   context = gx.get_context()
   
   validation_definition_name = "my_validation_definition"
   validation_definition = context.validation_definitions.get(validation_definition_name)
   ```

2. Execute the Validation Definition's `run()` method:

   ```python title="Python"
   validation_result = validation_definition.run()
   ```

   Validation Results are automatically saved in your Data Context when a Validation Definition's `run()` method is called.  For convenience, the `run()` method also returns the Validation Results as an object you can review.

   :::tip

   You can set the level of detail returned in a Validation Definition's results by passing a Result Format configuration as the `result_format` parameter of your Validation Definition's `run(...)` method.  For more information on Result Formats, see [Choose a result format](/core/trigger_actions_based_on_results/choose_a_result_format/choose_a_result_format.md).

   :::

3. Review the Validation Results:
 
   ```python title="Python"
   print(validation_result)
   ```
   
   When you print the returned Validation Result object you will recieve a yaml representation of the results.  By default this will include a `"results"` list that includes each Expectation in your Validation Definition's Expectation Suite, whether the Expectation was successfully met or failed to pass, and some sumarized information explaining the why the Expectation succeeded or failed.

   :::tip

   GX Cloud users can view the Validation Results in the GX Cloud UI by following the url provided with:

   ```python title="Python"
   print(validation_result.result_url)
   ```

   :::

</TabItem>

<TabItem value="sample_code" label="Sample code">

```python showLineNumbers title="Python"
import great_expectations as gx

context = gx.get_context()

validation_definition_name = "my_validation_definition"
validation_definition = context.validation_definitions.get(validation_definition_name)

# highlight-next-line
validation_result = validation_definition.run()

# highlight-next-line
print(validation_result)

# highlight-next-line
print(validation_result.results_url)
```

</TabItem>

</Tabs>