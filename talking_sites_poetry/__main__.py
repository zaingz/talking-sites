import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.vectorstores import FAISS
from langchain.document_loaders import AsyncHtmlLoader
from langchain.document_transformers import Html2TextTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

app = typer.Typer()
console = Console()

@app.command()
def ask(url: str):
    docs = getUrlDocs(url)
    store = getVectorStore(docs)

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Query")
    table.add_column("Response")

    console.print("[i grey37]Enter [u]q[/u] to exit anytime[/i grey37]")


    while True:  # Start an infinite loop
        query = Prompt.ask("\n[blue bold]>[/blue bold][red] Enter your query[/red]")

        if query.lower() == 'q': 
            break

        response = queryStoreLLM(store, query)
        console.print(f"[green]{response}[/green]")
        table.add_row(query, response)
    
    console.print(f"\n\n[bold grey37]Summary of conversation with [blue]{url}[/blue][/bold grey37]")
    console.print(table)
    raise typer.Exit()

def getUrlDocs(url):
    loader = AsyncHtmlLoader(url)
    docs = loader.load()
    html2text = Html2TextTransformer()
    docs_transformed = html2text.transform_documents(docs)
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=1000, 
                                                                    chunk_overlap=0)
    return splitter.split_documents(docs_transformed)


def getVectorStore(docs):
    vectorstore = FAISS.from_documents(docs, embedding=OpenAIEmbeddings())
    return vectorstore.as_retriever()

def queryStoreLLM(vectorStore, query):
    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

    model = ChatOpenAI()
    chain = (
        {"context": vectorStore, "question": RunnablePassthrough()} 
        | prompt 
        | model 
        | StrOutputParser()
    )
    return chain.invoke(query)



if __name__ == "__main__":
    app()
