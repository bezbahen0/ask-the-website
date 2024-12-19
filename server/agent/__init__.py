from server.agent.html_agent import HTMLAgent

def get_agent(page_type="text/html"):
    if page_type == "text/html":
        agent = HTMLAgent
    else:
        raise NotImplementedError(f"Agent with content type '{page_type}' not supported")
    return agent