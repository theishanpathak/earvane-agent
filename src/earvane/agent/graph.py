from langgraph.graph import StateGraph, START, END

from earvane.agent.state import ArtistState
from earvane.agent.nodes.signal_collector import signal_collector_node
from earvane.agent.nodes.relevance_scorer import relevance_scorer_node

def build_graph():
    """Wire Signal Collector -> Relevance Scorer into a LangGraph graph."""
    builder = StateGraph(ArtistState)

    builder.add_node("signal_collector", signal_collector_node)
    builder.add_node("relevance_scorer", relevance_scorer_node)

    builder.add_edge(START, "signal_collector")
    builder.add_edge("signal_collector", "relevance_scorer")
    builder.add_edge("relevance_scorer", END)

    return builder.compile()

if __name__ == "__main__":
    graph = build_graph()
    result = graph.invoke(ArtistState(artist_id=1, artist_name="Ariana Grande"))
    print(result)

