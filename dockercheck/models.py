from dataclasses import dataclass, field


@dataclass
class Instruction:
    keyword: str
    value: str
    line: int
    end_line: int
    original_keyword: str
    ignored: set[str] = field(default_factory=set)
    heredoc: bool = False


@dataclass
class Stage:
    index: int
    base: str
    alias: str
    start: Instruction
    instructions: list[Instruction] = field(default_factory=list)
    parent: "Stage | None" = None

    def effective(self, keyword):
        found = [i for i in self.instructions if i.keyword == keyword]
        return found[-1] if found else self.parent.effective(keyword) if self.parent else None


@dataclass
class Document:
    path: str
    source: str
    instructions: list[Instruction]
    stages: list[Stage]


@dataclass
class Finding:
    rule: str
    severity: str
    message: str
    recommendation: str
    line: int
    stage: str = ""
    fixable: bool = False


@dataclass
class Report:
    path: str
    findings: list[Finding]
    stages: int = 0
    suppressed: int = 0
