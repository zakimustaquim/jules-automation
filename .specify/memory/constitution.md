<!-- 
SYNC IMPACT REPORT

Version: 1.0.0 (NEW - initial constitution created)
Modified Principles: N/A (new)
Added Sections: Core Principles (5 principles), Anti-Patterns section, Governance
Removed Sections: None
Templates Updated:
  - plan-template.md: ✅ Reviewed - no changes needed (no overengineering gates present)
  - spec-template.md: ✅ Reviewed - principles align with flexibility
  - tasks-template.md: ✅ Reviewed - no mandatory testing gates that conflict
  
Rationale: Initial constitution emphasizing personal/for-fun project nature with pragmatism, fun-first values, and explicit anti-overengineering guidance.

-->

# Jules' Interesting App Automation Constitution

## Core Principles

### I. For-Fun & Personal
This is a personal, hobby project created for learning and enjoyment. There is NO production deadline, NO paying customers, and NO operational obligations. The goal is to explore ideas, experiment with technology, and have fun—not to build production-grade infrastructure.

**Non-negotiable**:
- Do not justify complexity with "production readiness" or "scalability"
- Do not implement features "just in case" we might need them later
- Abandon features mid-project if they stop being fun
- Prioritize personal satisfaction over best practices

### II. Pragmatism Over Perfectionism
Start simple and add complexity only when it creates immediate, tangible value. Incomplete or rough solutions are acceptable if they work well enough for a personal project.

**Non-negotiable**:
- YAGNI principle enforced: "You Aren't Gonna Need It"—don't build for hypothetical requirements
- Single-file scripts are acceptable; you don't need monorepos
- Hardcoded values are fine if they work; avoid premature abstraction
- Tech debt is acceptable if it unblocks momentum
- Skipping tests is acceptable if you're learning or prototyping

### III. Velocity Over Ceremony
Minimize process overhead. No mandatory code reviews, formal design documents, or lengthy meetings. Use the least friction path to getting working code.

**Non-negotiable**:
- No bureaucratic gates or approval workflows
- Commit messages can be casual; "fix stuff" is fine
- Refactoring can happen ad-hoc without formal sprints
- Documentation is optional unless you genuinely need it later

### IV. Learning-Driven
The primary metric of success is "Did I learn something interesting?" Pursuing technologies, patterns, or approaches that are educationally valuable is encouraged, even if they're not "the best" for the job.

**Non-negotiable**:
- Experimentation is always encouraged
- Dead ends and failed experiments are learning opportunities, not failures
- Adopt new tools or languages whenever curious—this is the whole point
- Document learnings, not requirements

### V. Maintainability Without Dogma
Write code that future-you (6 months from now) can understand and modify without excessive study. But don't obsess over extensibility or clean architecture—clarity matters more than cleverness.

**Non-negotiable**:
- Comments explaining *why*, not *what*—if code is confusing, clarify it
- Function names should be self-documenting
- Avoid clever one-liners that sacrifice readability
- Refactor ruthlessly when code feels confusing; procrastinating makes it worse

## Anti-Patterns (What NOT to Do)

These practices are actively discouraged:

- **"Enterprise Grade" Everything**: Do not implement microservices, message queues, databases, Docker orchestration, or CI/CD pipelines unless the project genuinely needs them
- **Premature Optimization**: Do not optimize performance, memory, or resource usage until something is actually slow
- **Over-Testing**: Do not write 100% test coverage or extensive mocking; integration tests only if you're debugging real bugs
- **Abstraction Creep**: Do not create base classes, interfaces, or factories for code that appears in only one place
- **Deferred Decisions**: Do not postpone technical choices waiting for "the right architecture"—pick something and move on

## Development Guidelines

- **Tech Decisions**: Choose tools based on curiosity, not industry trends
- **Documentation**: Write it only when you'd benefit from reading it later
- **Refactoring**: Improve code as you go if it bothers you; don't defer it indefinitely
- **Debugging**: Use `print()` / `console.log()` fearlessly; debuggers optional
- **Shipping**: "Done and shipped" beats "perfect but unfinished"

## Governance

**Constitution Primacy**: This constitution overrides all other project templates, guides, or conventions. When in doubt, ask: "Does this add fun or learning?" If no, don't do it.

**Amendment Process**: Amendments require only a brief note explaining the change (no formal approval needed). Update this file and move forward.

**Compliance Review**: No automated gates. If you feel the project is over-engineered, update the constitution to reduce constraints.

**Version Policy**: Use semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Removed a principle or fundamentally changed project goals
- **MINOR**: Added a new principle or materially expanded guidance
- **PATCH**: Clarifications, rewording, or non-semantic changes

**Runtime Guidance**: Refer to project-specific documentation (e.g., `.claude/commands/`) for execution workflows. This constitution sets values; those files operationalize them.

---

**Version**: 1.0.0 | **Created**: 2025-06-13 | **Last Amended**: 2026-01-16
