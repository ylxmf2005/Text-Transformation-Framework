# SecEval

This repo is a pipeline to generate evaluation questions for security evaluation tasks.

It's has following features:
1. load data from web pages or files, then parse the data into structured text artifacts, while maintaining the hierarchy of the data such as the directory structure of the files or the layout of the web pages. See [Load and Parse Data](#load-and-parse-data) for more details.
3. generate evaluation questions based on the parsed data. See [Generate Evaluation Questions](#generate-evaluation-questions) for more details.
4. evaluate the generated questions. See [Evaluate Generated Questions](#evaluate-generated-questions) for more details.


## Requirements

- [Python 3.10+](https://www.python.org/downloads/)
- [Poetry](https://python-poetry.org/docs/#installation)
- JDK 11+

## Install

```bash
poetry install
```


## Load and Parse Data 

### Data sources: 
Data sources are defined as loaders. Each loader is responsible for crawling data from a specific source. For examplem, the data source can be a web page or a file.

#### Available Loaders:
* [Web](seceval/loader/base/web.py)
* [File](seceval/loader/base/file.py)

### Parsers:
Parsers are used to parse the content of the data source. The parser is selected based on the content type of the data source. For example, if the data source is a markdown file, the [Markdown Parser](seceval/parser/md.py) will be used to parse the content.

### Available Parsers:

* [Markdown](seceval/parser/md.py)
* [Html](seceval/parser/html.py)
* [Pdf](seceval/parser/pdf.py)
* [Text](seceval/parser/text.py)
* [Xml](seceval/parser/xml.py)


### Develop a New Loader Class:
Create a new loader class within the seceval/loader directory. You should choose the appropriate base class for your new loader class based on the source type: for web sources, inherit from [WebLoader](seceval/loader/base/web.py); for file sources, inherit from [FileLoader](seceval/loader/base/file.py). Then, you have to initialize the class variables and methods.

#### WebLoader Variables and Methods
Extend WebLoader and configure the following class attributes:

* `loader_name: str` # The unique name to identify the loader.
* `base_url: str` # The root URL, which is used for handling relative path. 
* `start_urls: List[str]` # A list of URLs to start the crawling process.
* `max_depth: int` # The maximum depth to crawl from the start URLs.
* `batch_size: int = 30` # The number of URLs to process in a batch.
* `use_browser: bool = False` # Whether to use a browser environment for crawling, set this to True if the web page is rendered by JavaScript.

You can also provide override implement for the following methods:

* `def extract_url(self, html: str, current_url: str, depth: int) -> List[str]` , which is used to extract URLs from the HTML content.
* `def filter_url(self, url: str, parent_url: str, depth: int) -> bool` , which is used to decide if a URL should be crawled based on custom logic.

#### FileLoader Variables and Methods
When creating a subclass of FileLoader, set these attributes:

* `loader_name: str` # The unique name to identify the file loader.
* `dirname: str` # Directory path where the search for files begins.
* `filename_pattern: str` # Glob pattern to match filenames (e.g., '*.pdf').
* `recursive: bool (default is False)` # Whether to search directories recursively.

#### Common Loader Variables and Methods 

* `parser_profile: Dict[str, Any]` # A dictionary with parser configurations (e.g., for markdown or html content). You should setup the parser profile based on the content type of the source. For example, if the source is a markdown file, you should set the parser profile for the [Markdown Parser](seceval/parser/md.py). 

You can provide an override implement for the following methods:

* `def transform_content(self, content: TypedContent, depth: int) -> TypedContent` , which is used to transform the content before parsing. You can use this function to remove unwanted content (e.g., ads, navigation bars, etc.) from the content.
* `def filter_item(self, item: PageItem, depth: int) -> bool` , which is used to decide if an item should be parsed by the parser based on custom logic.



#### Example Loader Implementations
* WebLoader: [Mozilla Security](seceval/loader/mozilla_security.py)
* FileLoader: [Apple Platform Security](seceval/loader/apple_platform_security.py)

### Register the New Loader:

After successfully creating the new loader class, register this loader within the main function. To do this, add instances of your new loader class to the loaders list in the main function. This registration will guarantee that your new loader is executed when the main function is invoked.

### Run Loader

Start a poetry shell and run main.py

```bash
poetry shell
python seceval/main.py -l -t <task_name>
```

Or run main.py by poetry run

```bash
poetry run python -m seceval.main -l -t <task_name>
```

### Inspect the Loaded Data

#### Page Tree

The loaded data is stored in a Json file in the data directory. There will be two files for each loader: one for storing page tree and one for storing text_artifact parsed from the pages. 

The page tree is stored in a Json file named as `<loader_name>_pages.json`. The page tree is a list of pages, each page has following fields. 

* id: the unique id of the page
* parent_id: the id of the parent page in the page tree
* uri: the uri of the page, if it is a web page, it is the url of the page, if it is a file, it is the path of the file.
* depth: the depth of the page in the page tree
* type: the mime type of the page

The hierarchy of the page tree is determined by the layout of the web pages or the directory structure of the files.

For example, the following web page:

```html
<html>
  <head>
    <title>Page 1</title>
  </head>
  <body>
    <a href = url of Page 2 >
    <a href = url of Page 3 >
  </body>
</html>

<html>
  <head>
    <title>Page 2</title>
  </head>
  <body>
  </body>
</html>

<html>
  <head>
    <title>Page 3</title>
  </head>
  <body>
    <a href = url of Page 4 >
  </body>
</html>


<html>
  <head>
    <title>Page 4</title>
  </head>
  <body>
  </body>
</html>

<html>
  <head>
    <title>Page 5</title>
  </head>
  <body>
  </body>
</html>


```

The page tree is as follows:
* Page 1 (depth=1, parent_id=None)
  * Page 2 (depth=2, parent_id=id of Page 1)
  * Page 3 (depth=2, parent_id=id of Page 1)
    * Page 4 (depth=3, parent_id=id of Page 3)
* Page 5 (depth=1, parent_id=None)



#### Text Artifact

The text_artifact is stored in a Json file named as `<loader_name>.json`. The text_artifact is a list of text_artifact, each text_artifact has following fields: 

* page_id: the id of the page that contains the artifact
* page_url: the url of the artifact
* page_depth: the depth of the page
* page_type: the type of the page
* id: the unique id of the artifact
* parent_id: the id of the parent artifact
* index: the index of the artifact in the page
* level: the header level of the artifact
* title: the title of the artifact
* text: the text content of the artifact

The field index, level and parent_id are used to construct the artifact hierarchy. The artifact hierarchy is determined by the layout of the web page or markdown file. For example, the following markdown file:

```markdown
# Title 1
## Title 2
### Title 3
# Title 4
```
The artifact hierarchy is as follows:

* Title 1 (level=1, index=0, parent_id=None)
  * Title 2 (level=2, index=1, parent_id=id of Title 1)
    * Title 3(level=3, index=2, parent_id=id of Title 2)
* Title 4 (level=1, index=3, parent_id=None)

## Generate Evaluation Questions

### Prepare the Genration Prompt yaml file

The generation prompt yaml file is used to configure the generation prompt, which is used to generate evaluation questions. The generation prompt yaml file is stored in the `seceval/prompt/<task_name>.yaml` directory. As you can see in [prompt.py](seceval/question/prompt.py), the generation prompt yaml file has following fields: 

```
class QuestionGenerationPrompt(BaseModel):
    background: str = Field(description="文本背景")
    text: str = Field(description="文本内容")
    role: str = Field(description="角色")
    examination_focus: List[str] = Field(description="考查方向")
    task_description: str = Field(description="任务描述")
    requirements: List[str] = Field(description="出题要求")
    output_format: str = Field(description="输出格式")
    system_prompt_template: str = "default system prompt template"
    user_prompt_template: str = "default user prompt template"
```

An example of the generation prompt yaml file can be found [here](prompt/attck.yaml). 

### Generate Evaluation Questions

Start a poetry shell and run main.py

```bash
poetry shell
python seceval/main.py -g -t <task_name>
```

Or run main.py by poetry run

```bash
poetry run python -m seceval.main -g -t <task_name>
```

### Inspect the Generated Questions

Generated questions are stored in a Json file named as `<task_name>.json` in the question directory. The prompt used to generate the question is stored in a text file named as `<task_name>_prompt.txt` in the question directory. 

## Evaluation Generated Questions

### Prepare the Evaluation Prompt yaml file

The evaluation prompt yaml file is used to configure the evaluation prompt, which is used to evaluate the generated questions. The evaluation prompt yaml file is stored in the `seceval/prompt/<task_name>_eval.yaml` directory. As you can see in [prompt.py](seceval/question/prompt.py), the evaluation prompt yaml file has following fields: 


```
class QuestionEvaluationPrompt(BaseModel):
    question: str = Field(description="问题")
    # to be implemented

```

An example of the evaluation prompt yaml file can be found [here](prompt/attck_eval.yaml).

### Evaluate Generated Questions

Start a poetry shell and run main.py

```bash
poetry shell
python seceval/main.py -e -t <task_name>
```

Or run main.py by poetry run

```bash
poetry run python -m seceval.main -e -t <task_name>
```

### Inspect the Evaluation Results

Evaluation result are stored in a Json file named as `<task_name>_eval.json` in the question directory. The prompt used to evaluate the question is stored in a text file named as `<task_name>_eval_prompt.txt` in the question directory.