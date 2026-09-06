from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from .tools.sandbox_tools import sandbox_tools
from .tools.web_search_tool import WebSearchTool
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class EngineeringTeam:
    """EngineeringTeam crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    def __init__(self, llm):
        self.llm = llm

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_lead'],  # type: ignore[index]
            llm=self.llm,
            verbose=True,
            tools=[WebSearchTool()],
            max_iter=8,
            max_retry_limit=0,
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],  # type: ignore[index]
            llm=self.llm,
            verbose=True,
            tools=sandbox_tools,
            max_iter=10,
            max_retry_limit=0,
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['frontend_engineer'],  # type: ignore[index]
            llm=self.llm,
            verbose=True,
            tools=sandbox_tools,
            max_iter=10,
            max_retry_limit=0,
        )

    @agent
    def test_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['test_engineer'],  # type: ignore[index]
            llm=self.llm,
            verbose=True,
            tools=sandbox_tools,
            max_iter=12,
            max_retry_limit=0,
        )

    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_task']  # type: ignore[index]
        )

    @task
    def code_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_task'],  # type: ignore[index]
        )

    @task
    def frontend_task(self) -> Task:
        return Task(
            config=self.tasks_config['frontend_task'],  # type: ignore[index]
        )

    @task
    def test_task(self) -> Task:
        return Task(
            config=self.tasks_config['test_task'],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the EngineeringTeam crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            tracing=False,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
