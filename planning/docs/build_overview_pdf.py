"""Write the AgilePulse reader overview PDF."""

from pathlib import Path

from fpdf import FPDF

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUT = Path(__file__).with_name("scaled-engine-overview.pdf")

INK = (28, 36, 48)
MUTED = (78, 88, 100)
NAVY = (27, 54, 93)
GREEN = (28, 92, 64)
AMBER = (122, 78, 28)
LINE = (214, 220, 226)
WASH = (244, 246, 248)
GREEN_WASH = (232, 242, 236)
AMBER_WASH = (248, 242, 232)


class Overview(FPDF):
    def __init__(self):
        super().__init__(format="Letter", unit="mm")
        self.add_font("body", "", FONT)
        self.add_font("body", "B", FONT_B)
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(16, 16, 16)

    def footer(self):
        self.set_y(-12)
        self.set_font("body", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 6, "AgilePulse  ·  tool overview", align="L")
        self.cell(0, 6, str(self.page_no()), align="R")

    def ensure(self, height):
        if self.get_y() + height > self.h - 18:
            self.add_page()

    def h1(self, text):
        self.ensure(32)
        self.ln(2)
        self.set_font("body", "B", 14)
        self.set_text_color(*NAVY)
        self.multi_cell(0, 7, text)
        self.set_draw_color(*NAVY)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y() + 0.5, self.w - self.r_margin, self.get_y() + 0.5)
        self.ln(4)

    def h2(self, text):
        self.ensure(24)
        self.ln(1)
        self.set_font("body", "B", 11)
        self.set_text_color(*INK)
        self.multi_cell(0, 6, text)
        self.ln(1)

    def para(self, text):
        self.set_font("body", "", 10)
        width = self.w - self.l_margin - self.r_margin
        lines = self.multi_cell(width, 5.2, text, dry_run=True, output="LINES")
        self.ensure(len(lines) * 5.2 + 2)
        self.set_text_color(*INK)
        self.multi_cell(width, 5.2, text)
        self.ln(2)

    def bullet(self, text, color=NAVY):
        self.set_font("body", "", 10)
        width = self.w - self.l_margin - self.r_margin - 4
        lines = self.multi_cell(width, 5.2, text, dry_run=True, output="LINES")
        self.ensure(len(lines) * 5.2 + 2)
        self.set_text_color(*INK)
        x = self.l_margin
        y = self.get_y()
        self.set_fill_color(*color)
        self.rect(x, y + 1.6, 1.6, 1.6, style="F")
        self.set_x(x + 4)
        self.multi_cell(width, 5.2, text)
        self.ln(1.2)

    def step(self, number, title, text):
        self.set_font("body", "", 10)
        width = self.w - self.l_margin - self.r_margin - 10
        lines = self.multi_cell(width, 5.2, text, dry_run=True, output="LINES")
        self.ensure(7 + len(lines) * 5.2 + 3)
        y = self.get_y()
        self.set_fill_color(*NAVY)
        self.set_text_color(255, 255, 255)
        self.set_font("body", "B", 9)
        self.rect(self.l_margin, y, 8, 6, style="F")
        self.set_xy(self.l_margin, y + 0.6)
        self.cell(8, 5, str(number), align="C")
        self.set_xy(self.l_margin + 10, y)
        self.set_text_color(*NAVY)
        self.set_font("body", "B", 10)
        self.multi_cell(0, 5.2, title)
        self.set_x(self.l_margin + 10)
        self.set_font("body", "", 10)
        self.set_text_color(*INK)
        self.multi_cell(0, 5.2, text)
        self.ln(2)

    def band(self, title, lines, wash, accent):
        self.set_font("body", "", 10)
        height = 8 + len(lines) * 6
        self.ensure(height + 4)
        x = self.l_margin
        y = self.get_y()
        w = self.w - self.l_margin - self.r_margin
        self.set_fill_color(*wash)
        self.rect(x, y, w, height, style="F")
        self.set_fill_color(*accent)
        self.rect(x, y, 1.6, height, style="F")
        self.set_xy(x + 5, y + 2)
        self.set_font("body", "B", 10)
        self.set_text_color(*accent)
        self.cell(0, 5, title)
        self.set_font("body", "", 10)
        self.set_text_color(*INK)
        yy = y + 8
        for line in lines:
            self.set_xy(x + 5, yy)
            self.cell(0, 5, line)
            yy += 6
        self.set_y(y + height + 3)


def build():
    pdf = Overview()
    pdf.add_page()

    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, pdf.w, 36, style="F")
    pdf.set_xy(16, 10)
    pdf.set_font("body", "B", 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, "AgilePulse")
    pdf.set_xy(16, 20)
    pdf.set_font("body", "", 11)
    pdf.cell(0, 6, "Overview of the tool, the delivery process, and what a shop can skip")
    pdf.set_y(42)

    pdf.para(
        "AgilePulse is a local-first project tool for a shop that runs more than one team on the same product. "
        "The name is a working title. The process is a light form of scaled agile: shared outcomes, a short planning cycle, "
        "team delivery, and a review of evidence. Agent work uses that same process, with extra gates where a feature needs data or ships an agent."
    )
    pdf.para(
        "A person can hold more than one role. The steps do not merge. Before a task is saved, the tool asks which role the person is acting in."
    )

    pdf.h1("Features")
    pdf.h2("Organization")
    pdf.bullet("Portfolio, value stream, delivery group, and team.")
    pdf.bullet("Roles: stream owner, group facilitator, product manager, product owner, scrum master, technical lead, business stakeholder, and team member.")
    pdf.bullet("One person can hold several roles. Each saved task stores the acting role.")
    pdf.bullet("The delivery group can be a real group or a placeholder. The facilitator seat can be empty.")

    pdf.h2("Work")
    pdf.bullet("Goals, initiatives, features, and stories. An initiative moves through Proposed, Shaping, Ready, Active, and Done.")
    pdf.bullet("Work kinds: feature, platform item, prototype, and experiment.")
    pdf.bullet("A delivery path on every item: Discover, Define, Build, Check, Ship, with a history of moves.")
    pdf.bullet("A shared done list. Check cannot finish while a required item on that list is open.")
    pdf.bullet("A team board with a work-in-progress limit. A new start is refused when the board is full.")

    pdf.h2("Planning and learning")
    pdf.bullet("A planning cycle, six weeks unless the group chooses other dates.")
    pdf.bullet("Group outcomes and team outcomes, milestones, dependencies, risks, and a confidence check.")
    pdf.bullet("Each dependency has an owner, a needed-by date, and an open date. The providing team is optional.")
    pdf.bullet("Dependent work only when a feature needs another team: what must change, what done looks like, and a needed-by date. The shop may name the team or leave it blank.")
    pdf.bullet("An architecture review, and a PII review, only on features that say the review applies.")
    pdf.bullet("Iteration board, team sync, cross-team note, and a retrospective that stays on the team.")
    pdf.bullet("An evidence review at each iteration boundary: what was observed, then what will change.")

    pdf.h2("Measures and controls")
    pdf.bullet("A delay-cost score for sorting the backlog, from value, urgency, risk or opportunity, and size.")
    pdf.bullet("Story sizing by team: t-shirt sizes or points. T-shirt labels start at 1, 2, 3, 5, and 8, and the team can change those numbers.")
    pdf.bullet("Team velocity: the estimate completed in an iteration, with the last three iterations visible.")
    pdf.bullet("Throughput, lead time, work in progress, active time versus wait, work mix, and outcome reliability.")
    pdf.bullet("Policies that can block a stage change. An evidence log of who acted, person or agent.")
    pdf.bullet("Acceptance fields for a threshold, a dataset label, and a latency target.")

    pdf.h2("Agents, data, and shop setup")
    pdf.bullet("A timeboxed research item with one question: prompt, deeper agent, or data. The result is proceed, reshape, or drop.")
    pdf.bullet("A feature that needs data cannot enter Build until that data check proceeds, or a product owner records an exception.")
    pdf.bullet("An agent feature records a risk tier, the tools it may call, a held-out eval reference, who can stop it, and a rollback drill.")
    pdf.bullet("A prompt or model change sends the feature back to Check. An incident marks the agent advisory and can add an eval case.")
    pdf.bullet("SQLite on a laptop. A shop can switch to PostgreSQL, SQL Server, Oracle, or another SQL database through an adapter.")
    pdf.bullet("Local login and JWT. Roles stay in this database. A shop can replace the login with its own code.")
    pdf.bullet("A plugin for the shop's own tool. Cursor, Claude, or another product can submit notes and documents as proposed initiatives. The product owner accepts them for the scrum master and the team.")
    pdf.bullet("A story pack exported for that same tool, so developers can ask it to write code. The code stays in the shop's repository.")
    pdf.bullet("A short in-app tutorial and a guide a product manager can read away from the screen.")

    pdf.h1("Process steps")
    pdf.para(
        "The steps below are the whole loop. A small shop does not get a shorter loop. It leaves optional seats empty and still walks the steps that remain."
    )

    pdf.h2("Set up once")
    pdf.step("1", "Name the stream and the teams", "Create a portfolio, a value stream, and at least one team. Create a delivery group, or accept the placeholder that stands in for one.")
    pdf.step("2", "Assign roles", "Give each person the roles they will act in. A product manager may also be product owner and scrum master. Add group facilitator only if someone will manage the group.")

    pdf.h2("Open a planning cycle")
    pdf.step("3", "Align on outcomes", "In one short session, record group outcomes, team outcomes, milestones, risks, and a confidence check. Give every dependency an owner and a needed-by date. Name a providing team only if you want to.")
    pdf.step("4", "Write dependent work when it applies", "If a feature needs a firewall change, database access, or any other team, write what must be done, what done looks like, and the needed-by date. Use a team name you already created, or leave the team blank. One team may cover more than one kind of access. Skip this step when no other team is involved. Mark an architecture review or a PII review only on the features that need them.")
    pdf.step("5", "Plan inside each team", "Each team opens an iteration inside the cycle, estimates its stories in t-shirt sizes or points, and orders its own backlog. The shared session does not plan every task.")

    pdf.h2("Move one piece of work")
    pdf.step("6", "Discover", "Write the problem and the outcome the work is for.")
    pdf.step("7", "Research, when the work needs it", "If the feature needs data, or may use an agent, open a research item. Set a clock, five days unless you choose otherwise. At the end, record proceed, reshape, or drop. A deeper-agent question waits until a prompt question has failed.")
    pdf.step("8", "Define", "Write the bounded intent. A person approves it. That approval is the limit of what the team or an agent may do.")
    pdf.step("9", "Build", "Build starts only after Define is approved. If the feature needs data, Build also waits for a data decision of proceed, or for a recorded exception.")
    pdf.step("10", "Check", "Someone other than the producer completes Check. The shared done list must be clear: integrated, acceptance met, and no dependency left without an owner. An architecture review or a PII review blocks Check only when the feature said that review applies and it is still open.")
    pdf.step("11", "Ship", "A named person decides to ship. A passing check is evidence for that decision. It is not the decision. Prototypes and experiments stop at Check unless someone explicitly ships them.")

    pdf.h2("During the iteration")
    pdf.step("12", "Act as product owner", "Order the backlog and accept a story only while acting as product owner.")
    pdf.step("13", "Act as scrum master", "Write the team sync, an impediment, or the retrospective only while acting as scrum master. The retro stays on the team unless the team promotes one learning.")
    pdf.step("14", "Name cross-team issues", "In the cross-team note, record the impediment or dependency and which team is asked to respond. Naming the team is optional.")
    pdf.step("15", "Respect the work-in-progress limit", "Do not start another item while the board is at its limit. The scrum master can raise the limit for one item by recording a reason.")

    pdf.h2("At the iteration boundary")
    pdf.step("16", "Review the evidence", "Record what was observed: a count, a customer comment, a demo note. Then record a decision: continue, drop, reshape, or resize. The count can include the iteration's velocity.")
    pdf.step("17", "Leave private notes private", "Raw retrospective text is not copied into the evidence review. Only a learning the team promotes can be attached.")

    pdf.h2("After an agent ships")
    pdf.step("18", "Re-check when the agent changes", "A new prompt version or model version returns the feature to Check.")
    pdf.step("19", "Handle an incident", "Mark the agent advisory until a person closes the incident. Add the failed case to the eval reference.")

    pdf.h1("What is required")
    pdf.para("These stay in place for a two-team shop and for a larger one. Skipping them would be a different process.")

    pdf.h2("Always")
    pdf.bullet("A value stream and at least one team.", GREEN)
    pdf.bullet("A delivery-group record, even when it is only a placeholder. Cycles and dependencies need a parent.", GREEN)
    pdf.bullet("A product owner for backlog order and story acceptance.", GREEN)
    pdf.bullet("A scrum master for the team sync, impediments, and the retrospective.", GREEN)
    pdf.bullet("An acting role on every saved task. The person switches to the role the task belongs to.", GREEN)
    pdf.bullet("For work that will ship: Discover, an approved Define, Build, an independent Check, and a human Ship.", GREEN)
    pdf.bullet("The shared done list, clear before Check can finish.", GREEN)
    pdf.bullet("An owner and a needed-by date on every dependency that is written down. The providing team may be blank.", GREEN)
    pdf.bullet("A sizing method on each team, t-shirt or points, and an estimate on each story that team plans.", GREEN)
    pdf.bullet("A work-in-progress limit on the team board.", GREEN)
    pdf.bullet("An evidence record of who acted, and whether they were a person or an agent.", GREEN)

    pdf.h2("When the feature needs data")
    pdf.bullet("A data research item with a timebox and a decision. Build stays closed on drop. Proceed requires a sample, access, and a named owner.", GREEN)
    pdf.bullet("An exception, with a reason, if a product owner moves the feature forward without that decision. The exception stays visible.", GREEN)

    pdf.h2("When the feature ships an agent")
    pdf.bullet("A risk tier: assistive, read-only, changes data, or high impact.", GREEN)
    pdf.bullet("The list of tools the agent may call, and which actions still need a person.", GREEN)
    pdf.bullet("A held-out eval reference. These are cases the prompt was not written against. A failed critical case blocks Ship.", GREEN)
    pdf.bullet("A named person who can stop the agent, and a note that rollback of the prompt, the tool list, and the policy was drilled.", GREEN)
    pdf.bullet("A return to Check when the prompt version or the model version changes.", GREEN)

    pdf.h1("What can be skipped")
    pdf.para(
        "Skipping here means the same process with an empty seat or a step that does not apply. It does not mean a second, lighter method."
    )

    pdf.h2("Optional inside the process")
    pdf.bullet("Dependent work. Leave it off when no other team has to act. When you write it, the team name is still optional.", AMBER)
    pdf.bullet("An architecture review, and a PII compliance review. Both stay off unless the feature needs that review.", AMBER)
    pdf.bullet("A dedicated group facilitator. Leave the seat empty. Tasks that manage the group turn off. Team steps stay.", AMBER)
    pdf.bullet("A fully staffed delivery group. Use the placeholder. Turn it into an active group later without moving the teams or the cycles.", AMBER)
    pdf.bullet("Shipping a prototype or an experiment. They end at Check unless someone chooses to ship.", AMBER)
    pdf.bullet("A deeper-agent research item, until a prompt trial has failed its question.", AMBER)
    pdf.bullet("A second research question on work that is ordinary delivery and does not need data or an agent.", AMBER)
    pdf.bullet("Cloud login. Local login is enough to run the tool. JWT is available when a shop wants it.", AMBER)
    pdf.bullet("A shop database on the first day. SQLite is the local default. PostgreSQL, SQL Server, Oracle, or another SQL adapter can wait.", AMBER)

    pdf.h2("Not in this tool")
    pdf.para("These are real practices. They belong in other systems. AgilePulse stores the decision and the gate, not the runtime.")
    pdf.bullet("Running a model, storing prompt text, scoring an eval, or hosting the agent's tools.", AMBER)
    pdf.bullet("Token-cost accounting, penetration tests, and a security program.", AMBER)
    pdf.bullet("Azure AD and AWS IAM as built-in logins. A shop may replace the authenticator with its own code. Roles still live in this database.", AMBER)
    pdf.bullet("Calling Cursor, Claude, or any other model. The shop's tool does that, then pushes a proposal in. Their source repository is never opened.", AMBER)
    pdf.bullet("In-product helpers that draft dependencies, splits, scores, or risk states. A shop that already has a tool uses the plugin instead.", AMBER)
    pdf.bullet("Funding guardrails and an investment workshop.", AMBER)
    pdf.bullet("A separate fast engine, and a container image, until a measured path needs them.", AMBER)
    pdf.bullet("A course, quizzes, or certificates. Training is the in-app tutorial plus this overview.", AMBER)

    pdf.ln(2)
    pdf.band(
        "The rule for a small shop",
        [
            "Same person, same steps. A product manager may be product owner and scrum master.",
            "Backlog work is still done as product owner. The retro is still done as scrum master.",
            "Managing the group is still done as facilitator, or that seat stays empty.",
        ],
        WASH,
        NAVY,
    )

    pdf.output(str(OUT))
    print(OUT)


if __name__ == "__main__":
    build()
