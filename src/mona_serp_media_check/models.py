"""Cac kieu du lieu dung chung cho toan bo cong cu."""

from __future__ import annotations

from dataclasses import dataclass, field


# Ba muc do nghiem trong cua mot phat hien:
#   fail -> loi that su, se lam script tra ve exit code khac 0
#   warn -> dang nghi ngo / nen sua nhung khong chan
#   pass -> kiem tra da qua, chi dung de bao cao day du
SEVERITIES = ("fail", "warn", "pass")


@dataclass
class Finding:
    """Mot ket qua kiem tra don le (1 quy tac x 1 doi tuong)."""

    severity: str
    group: str
    code: str
    message: str

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"severity khong hop le: {self.severity}")

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "group": self.group,
            "code": self.code,
            "message": self.message,
        }


@dataclass
class Report:
    """Tong hop toan bo Finding cua mot lan quet."""

    url_or_path: str
    keyword: str
    findings: list[Finding] = field(default_factory=list)

    def add(self, severity: str, group: str, code: str, message: str) -> None:
        self.findings.append(Finding(severity, group, code, message))

    def extend(self, findings: list[Finding]) -> None:
        self.findings.extend(findings)

    @property
    def fail_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "fail")

    @property
    def warn_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "warn")

    @property
    def pass_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "pass")

    @property
    def is_ok(self) -> bool:
        return self.fail_count == 0

    def to_dict(self) -> dict:
        return {
            "target": self.url_or_path,
            "keyword": self.keyword,
            "summary": {
                "fail": self.fail_count,
                "warn": self.warn_count,
                "pass": self.pass_count,
            },
            "findings": [f.to_dict() for f in self.findings],
        }
