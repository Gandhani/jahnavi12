import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import TechnicalTag from '../../../../../reference/learn/term_tags/_tag.mdx';

Verify your new <TechnicalTag tag="datasource" text="Data Source" /> by loading data from it into a <TechnicalTag tag="validator" text="Validator" /> using a `BatchRequest`.

<Tabs
  defaultValue='runtime_batch_request'
  values={[
  {label: 'Using a SQL query', value:'runtime_batch_request'},
  {label: 'Using a table name', value:'batch_request'},
  ]}>
  
<TabItem value="runtime_batch_request">

Here is an example of loading data by specifying a SQL query.

```python name="docs/docusaurus/docs/snippets/redshift_yaml_example.py load data with query"
```

</TabItem>

<TabItem value="batch_request">

Here is an example of loading data by specifying an existing table name.

```python name="docs/docusaurus/docs/snippets/redshift_python_example.py load data with table name"
```

</TabItem>

</Tabs>