from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.pydantic_v1 import BaseModel


load_dotenv()


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]
    ask_human: bool


class RequestAssistance(BaseModel):
    """Escalate the conversation to an expert. Use this if you are unable to assist directly or if the user requires support beyond your permissions.

    To use this function, relay the user's 'request' so the expert can provide the right guidance.
    """

    request: str


memory = SqliteSaver.from_conn_string(":memory:")
graph_builder = StateGraph(State)
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
)
tool = TavilySearchResults(max_results=2)
tools = [tool]
llm_with_tools = llm.bind_tools(tools + [RequestAssistance])


def chatbot(state: State):
    response = llm_with_tools.invoke(state["messages"])
    ask_human = False
    if (
        response.tool_calls
        and response.tool_calls[0]["name"] == RequestAssistance.__name__
    ):
        ask_human = True
    return {"messages": [response], "ask_human": ask_human}


def create_response(response: str, ai_message: AIMessage):
    return ToolMessage(
        content=response,
        tool_call_id=ai_message.tool_calls[0]["id"],
    )


def human_node(state: State):
    new_messages = []
    if not isinstance(state["messages"][-1], ToolMessage):
        # Typically, the user will have updated the state during the interrupt.
        # If they choose not to, we will include a placeholder ToolMessage to
        # let the LLM continue.
        new_messages.append(
            create_response("No response from human.", state["messages"][-1])
        )
    return {
        # Append the new messages
        "messages": new_messages,
        # Unset the flag
        "ask_human": False,
    }


def select_next_node(state: State):
    if state["ask_human"]:
        return "human"
    # Otherwise, we can route as before
    return tools_condition(state)


# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools)
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("human", human_node)
graph_builder.add_conditional_edges(
    "chatbot",
    select_next_node,
    {"human": "human", "tools": "tools", END: END},
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge("human", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile(
    checkpointer=memory,
    interrupt_before=["human"],
    # Note: can also interrupt __after__ actions, if desired.
    # interrupt_after=["tools"]
)


# We can use this to generate a graph of the state machine
# from IPython.display import Image, display

# try:
#     display(Image(graph.get_graph().draw_mermaid_png()))
# except Exception:
#     # This requires some extra dependencies and is optional
#     pass

# config = {"configurable": {"thread_id": "1"}}
# **1. Chat**
# while True:
#     user_input = input("User: ")
#     if user_input.lower() in ["quit", "exit", "q"]:
#         print("Goodbye!")
#         break
#     for event in graph.stream(
#         {"messages": [("user", user_input)]}, config, stream_mode="values"
#     ):
#         event["messages"][-1].pretty_print()
#         # for value in event.values():
#             # if isinstance(value["messages"][-1], BaseMessage):
#             #     print("Assistant:", value["messages"][-1].content or value["messages"][-1].tool_calls)


# **2. Update chat state**
# user_input = "Do you know Qitaihe GDP?"
# # The config is the **second positional argument** to stream() or invoke()!
# events = graph.stream({"messages": [("user", user_input)]}, config)
# for event in events:
#     if "messages" in event:
#         event["messages"][-1].pretty_print()

# snapshot = graph.get_state(config)
# existing_message = snapshot.values["messages"][-1]
# print("Original")
# print("Message ID", existing_message.id)
# print(existing_message.tool_calls[0])
# new_tool_call = existing_message.tool_calls[0].copy()
# new_tool_call["args"]["query"] = "Is Qitaihe NB?"
# new_message = AIMessage(
#     content=existing_message.content,
#     tool_calls=[new_tool_call],
#     # Important! The ID is how LangGraph knows to REPLACE the message in the state rather than APPEND this messages
#     id=existing_message.id,
# )
# print("Updated")
# print(new_message.tool_calls[0])
# print("Message ID", new_message.id)
# graph.update_state(config, {"messages": [new_message]})

# answer = (
#     "Qitaihe GDP is 6.5 trillion RMB in 2020."
# )
# new_messages = [
#     # The LLM API expects some ToolMessage to match its tool call. We'll satisfy that here.
#     ToolMessage(content=answer, tool_call_id=existing_message.tool_calls[0]["id"]),
#     # And then directly "put words in the LLM's mouth" by populating its response.
#     AIMessage(content=answer),
# ]
# new_messages[-1].pretty_print()
# graph.update_state(
#     # Which state to update
#     config,
#     # The updated values to provide. The messages in our `State` are "append-only", meaning this will be appended
#     # to the existing state. We will review how to update existing messages in the next section!
#     {"messages": new_messages},
# )
# print("\n\nLast 2 messages;")
# print(graph.get_state(config).values["messages"][-2:])

# Add an update and tell the graph to treat it as if it came from the "chatbot".
# graph.update_state(
#     config,
#     {"messages": [AIMessage(content="I'm an AI expert!")]},
#     # Which node for this function to act as. It will automatically continue
#     # processing as if this node just ran.
#     as_node="chatbot",
# )
# snapshot = graph.get_state(config)
# print(snapshot.values["messages"][-3:])
# print(snapshot.next)


# **3. Human state**
user_input = "I need some expert guidance for building this AI agent. Could you request assistance for me?"
config = {"configurable": {"thread_id": "1"}}
# The config is the **second positional argument** to stream() or invoke()!
events = graph.stream(
    {"messages": [("user", user_input)]}, config, stream_mode="values"
)
for event in events:
    if "messages" in event:
        event["messages"][-1].pretty_print()

snapshot = graph.get_state(config)
ai_message = snapshot.values["messages"][-1]
human_response = (
    "We, the experts are here to help! We'd recommend you check out LangGraph to build your agent."
    " It's much more reliable and extensible than simple autonomous agents."
)
tool_message = create_response(human_response, ai_message)
graph.update_state(config, {"messages": [tool_message]})
# print(graph.get_state(config).values["messages"])

events = graph.stream(None, config, stream_mode="values")
for event in events:
    if "messages" in event:
        event["messages"][-1].pretty_print()
