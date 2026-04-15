# NewsPull
A workflow to automate gathering news and AI according to user preference


Agent will be built using the AGNO Library

-Orchestrator Agent:
    "this agent will control the workflow and call agents:
    There will be a reference page which details how many sources for the agent to look at, this agent role
is to call multiple instances of gathering Agents and delegate sources for the gather agent to gather.
Then it will determine a number of Digesting agent to summarize the information.
Then the summary will be pass to the tasting agent.
The tasting agent will return an article, if it is flagged show it to the user after presenting the credible information
Then prompt the user if they want to review the performance if they do call the feed back agent.
"

-Gathering Agent:
    "this agent will have 1 tool: webcrawling which will use the 
mcp-playwright skill that claude has. This agent will crawl each domain within a reference list:
reference list may include: reddit/forum, youtube/certain_channel, getnews, twitter/certain_user, tldrnews.
If the reference list is empty please prompt user to get reference, the reference list will also include
user preference such as AI, Agentic, Agents, Machine Learning. Do search based on those terms and similar keywords.
Retrieve the latest news that is not already retrieved previously. Keep track of previously gathered links"


-Digesting Agent:
    "This Agent will compress and distill information from the Gathering Agent.
the agent will keep the information short and accurate. The language the agent use will be simple
and explained and dissect difficult concepts"

-Tasting Agent :
    "This agent main purpose is to overlook at the reviews and the information presented. This agent
will fact-check and make sure that all new information gathered are accurate and credible. This agent
will rate the summary presented by usefulness to the user and credibility. If it is not usefull or credible
flag the article."

-Feedback Agent:
    " this agent will be trigger when the user is unhappy and would like to add certain changes to the system
this agent will help the user through various questions about the other 3 agents such as:
"are you happy with the language used?", always allowed the user to provide custom prompt
When the user express their dissatisfaction allow this agent to edit the file containing user reference/preferences in
regard to NewsPull and allow this agent to edit: digesting agent file, tasting agent file and gathering agent
such that the edit will support the changes that the user wants"

interface: this repo