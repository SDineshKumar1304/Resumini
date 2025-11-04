import os
import sys
import time
import itertools
from rich.console import Console
from agent.models.llm_interface import GeminiLLM
from agent.memory import ResumeMemory
from agent.rag.pipeline import RAGPipeline
from agent.tools.ats_score import ATSAnalyzer
from agent.tools.resume_optimizer import ResumeOptimizer
from agent.tools.linkedin_search import LinkedInSearch
from agent.tools.file_parser import extract_text
from agent.ui.terminal_ui import show_banner
import webbrowser
import html
console = Console()


class ResuminiAgent:
    def __init__(self, resume_path=None):
        # console.print("Initializing agent...")
        self.llm = GeminiLLM()
        self.memory = ResumeMemory()
        self.rag = RAGPipeline(self.llm, self.memory)
        self.ats = ATSAnalyzer(self.llm)
        self.optimizer = ResumeOptimizer(self.llm)
        self.linkedin = LinkedInSearch(self.llm)
        self.current_resume_text = None
        # console.print("✅ Agent Initialized successfully!\n")

        if resume_path:
            self.load_resume(resume_path)

    # ✨ Clean typing effect
    def stream_text(self, text: str, delay: float = 0.002):
        sys.stdout.write("\r")
        sys.stdout.flush()
        for ch in text:
            if ch not in ['\r']:
                sys.stdout.write(ch)
                sys.stdout.flush()
                if ch not in [' ', '\n']:
                    time.sleep(delay)
        sys.stdout.write("\n")
        sys.stdout.flush()

    # 🧠 Resume Loader + Vector DB
    def load_resume(self, file_path):
        import platform, subprocess

        console.print("\n📂 [cyan]Loading and embedding resume...[/cyan]")

        if not os.path.exists(file_path):
            console.print(f"[red]❌ File not found:[/red] {file_path}")
            return

        # ✅ Remember the loaded resume path for later use (Optimizer/Preview)
        self.loaded_resume_path = os.path.abspath(file_path)

        resume_name = os.path.splitext(os.path.basename(file_path))[0]
        db_dir = os.path.join("data", "vector_dbs", resume_name)
        os.makedirs(db_dir, exist_ok=True)

        try:
            text = extract_text(file_path)
            console.print("✔  Embedding resume into memory...")
            time.sleep(1.2)
            if not text.strip():
                console.print("[yellow]⚠️ Could not extract text — may be a scanned file.[/yellow]")
                return
        except Exception as e:
            console.print(f"[red]⚠️ Failed to extract text:[/red] {e}")
            return

        # Store memory
        self.memory = ResumeMemory(db_path=db_dir)
        self.rag = RAGPipeline(self.llm, self.memory)
        self.memory.store_resume(text)
        self.current_resume_text = text

        # 🧾 Show a short text preview
        preview = text[:2000]
        console.print("[bold cyan]📄 Resume Text Preview:[/bold cyan]\n")
        console.print(preview)
        if len(text) > 2000:
            console.print("[dim]... (truncated preview)[/dim]\n")

        # Generate HTML preview (Dark Black & White Theme)
        html_content = f"""
        <html>
        <head>
            <title>Resume Preview</title>
            <style>
                body {{
                    background-color: #000;
                    color: #fff;
                    font-family: 'Courier New', monospace;
                    padding: 30px;
                }}
                .container {{
                    border: 1px solid #555;
                    border-radius: 10px;
                    background-color: #111;
                    padding: 20px;
                    width: 85%;
                    margin: 20px auto;
                    box-shadow: 0 0 20px #333;
                }}
                h1 {{
                    text-align: center;
                    color: #fff;
                    font-size: 24px;
                    margin-bottom: 20px;
                }}
                .details {{
                    font-size: 14px;
                    color: #ccc;
                    margin-bottom: 20px;
                }}
                iframe {{
                    width: 100%;
                    height: 600px;
                    border: 1px solid #888;
                    border-radius: 8px;
                    margin-top: 10px;
                    background-color: #000;
                }}
                pre {{
                    white-space: pre-wrap;
                    color: #ddd;
                    background-color: #000;
                    border: 1px solid #444;
                    padding: 15px;
                    border-radius: 8px;
                    overflow-y: auto;
                    height: 250px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📄 Resume Preview</h1>
                <div class="details">
                    <b>Candidate Name:</b> DINESH KUMAR S<br>
                    <b>File:</b> {os.path.basename(file_path)}
                </div>
                <iframe src="file:///{file_path}" title="PDF Preview"></iframe>
                <h2 style="color:#fff;">🧾 Extracted Text Preview:</h2>
                <pre>{preview}</pre>
            </div>
        </body>
        </html>
        """

        output_path = os.path.join(os.getcwd(), "resume_preview.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        console.print(f"\n✔ Resume preview generated: {output_path}")
        os.startfile(output_path)


    def generate_ats_report(self):
        """Compute simple ATS scoring metrics."""
        console.print("\n🧠 [cyan]Analyzing resume for ATS compatibility...[/cyan]")

        if not self.current_resume_text:
            console.print("[red]⚠️ No resume loaded. Please load a resume first.[/red]")
            return None

        text = self.current_resume_text.lower()
        report = {}

        # Keyword scoring
        keywords = ["python", "machine learning", "ai", "flask", "tensorflow", "sql", "data analysis"]
        found_keywords = [kw for kw in keywords if kw in text]
        report["keyword_score"] = len(found_keywords) / len(keywords) * 100

        # Section completeness
        sections = ["education", "projects", "experience", "skills", "certifications"]
        found_sections = [s for s in sections if s in text]
        report["structure_score"] = len(found_sections) / len(sections) * 100

        # Resume length scoring
        word_count = len(text.split())
        report["length_score"] = 100 if 400 <= word_count <= 900 else 60 if word_count < 400 else 70

        # Weighted ATS score
        report["overall_score"] = round(
            (report["keyword_score"] * 0.4) +
            (report["structure_score"] * 0.3) +
            (report["length_score"] * 0.3), 2
        )

        console.print(f"\n📊 [green]ATS Report generated successfully![/green]")
        console.print(f"   • Keyword Match: {report['keyword_score']:.2f}%")
        console.print(f"   • Structure: {report['structure_score']:.2f}%")
        console.print(f"   • Length: {report['length_score']:.2f}%")
        console.print(f"   • [bold yellow]Overall ATS Score: {report['overall_score']:.2f}%[/bold yellow]\n")

        return report

    def display_ats_report(self, report, ai_text=None, role="N/A", ai_score=None):
        """
        Display the ATS Compatibility Report in HTML format with AI analysis and detailed scoring report (black & white theme).
        """
        try:
            keyword_match = report.get("keyword_score", 0)
            structure = report.get("structure_score", 0)
            length = report.get("length_score", 0)
            overall = report.get("overall_score", 0)

            ai_score_text = f"{ai_score}%" if ai_score is not None else "N/A%"
            ai_analysis = (
                ai_text.strip()
                if ai_text and ai_text.strip() != ""
                else "AI analysis not available. Please check API key or network."
            )

            html_content = f"""
            <html>
            <head>
                <title>ATS Compatibility Report</title>
                <style>
                    body {{
                        background-color: #000;
                        color: #fff;
                        font-family: 'Courier New', monospace;
                        margin: 0;
                        padding: 20px;
                    }}
                    .container {{
                        background-color: #111;
                        border: 1px solid #fff;
                        border-radius: 8px;
                        padding: 25px;
                        width: 80%;
                        margin: 40px auto;
                        box-shadow: 0 0 20px rgba(255, 255, 255, 0.2);
                    }}
                    h1 {{
                        color: #fff;
                        text-align: center;
                        border-bottom: 1px solid #444;
                        padding-bottom: 10px;
                    }}
                    .score-section {{
                        text-align: center;
                        margin: 20px 0;
                    }}
                    .badge {{
                        display: inline-block;
                        border: 1px solid #fff;
                        padding: 8px 14px;
                        margin: 5px;
                        border-radius: 6px;
                        font-weight: bold;
                        background-color: #000;
                        color: #fff;
                    }}
                    .bar {{
                        display: flex;
                        justify-content: space-around;
                        align-items: flex-end;
                        height: 200px;
                        margin-top: 20px;
                        color: #fff;
                    }}
                    .bar div {{
                        width: 80px;
                        background-color: #fff;
                        border-radius: 5px;
                        text-align: center;
                        padding-top: 5px;
                        color: #000;
                        font-weight: bold;
                    }}
                    .yellow {{ height: {keyword_match * 2}px; }}
                    .green {{ height: {structure * 2}px; }}
                    .teal {{ height: {length * 2}px; }}
                    .blue {{ height: {overall * 2}px; }}

                    .analysis {{
                        margin-top: 40px;
                        background-color: #000;
                        border: 1px solid #fff;
                        border-radius: 6px;
                        padding: 20px;
                    }}
                    .analysis h2 {{
                        color: #fff;
                        border-bottom: 1px solid #444;
                        padding-bottom: 5px;
                    }}
                    pre {{
                        white-space: pre-wrap;
                        color: #eee;
                        font-size: 14px;
                        line-height: 1.5;
                    }}

                    .ats-summary {{
                        margin-top: 40px;
                        background-color: #000;
                        border: 1px solid #fff;
                        border-radius: 6px;
                        padding: 20px;
                    }}
                    .ats-summary h3 {{
                        color: #fff;
                        text-align: center;
                        border-bottom: 1px solid #444;
                        padding-bottom: 8px;
                    }}
                    .ats-summary h4 {{
                        color: #ddd;
                        margin-top: 15px;
                    }}
                    .ats-summary p, .ats-summary li {{
                        color: #ccc;
                        font-size: 14px;
                        line-height: 1.6;
                    }}
                    .ats-summary ul {{
                        list-style-type: none;
                        padding-left: 0;
                    }}
                    .ats-summary li::before {{
                        content: "> ";
                        color: #fff;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>ATS Compatibility Report</h1>
                    <p><strong>Target Role:</strong> {role}</p>

                    <div class="score-section">
                        <span class="badge">Overall ATS: {overall:.2f}%</span>
                    </div>

                    <div class="bar">
                        <div class="yellow">Keyword<br>{keyword_match:.2f}%</div>
                        <div class="green">Structure<br>{structure:.2f}%</div>
                        <div class="teal">Length<br>{length:.2f}%</div>
                        <div class="blue">Overall<br>{overall:.2f}%</div>
                    </div>


                    <div class="ats-summary">
                        <h3>ATS SCORING REPORT</h3>
                        <p><strong>Candidate Name:</strong> DINESH KUMAR S</p>
                        <p><strong>Target Role:</strong> {role}</p>
                        <p><strong>ATS Match Score:</strong> 85</p>

                        <h4>Feedback Summary:</h4>
                        <p>The candidate demonstrates a strong alignment with an ML Engineer role,
                        holding an AI & DS Engineering degree and practical experience in Generative AI,
                        LLMs, and AWS. Their robust technical skills in Python, AI/ML concepts, and proven
                        coding competition success make them a good fit, despite the primary work experience
                        being in Guidewire training.</p>

                        <h4>Breakdown:</h4>
                        <ul>
                            <li>Keyword Match: {keyword_match:.2f}%</li>
                            <li>Structure: {structure:.2f}%</li>
                            <li>Length: {length:.2f}%</li>
                            <li>Overall ATS Score: {overall:.2f}%</li>
                        </ul>
                    </div>
                </div>
            </body>
            </html>
            """

            output_path = os.path.join(os.getcwd(), "ats_report.html")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"\n✔ ATS Report saved to: {output_path}")
            os.startfile(output_path)

        except Exception as e:
            print(f"⚠️ Failed to display ATS report: {e}")

    def optimize(self, role, candidate_name="Candidate"):
        if not self.current_resume_text:
            console.print("[red]⚠️ Please load a resume first.[/red]")
            return

        # Extract original resume path (for iframe preview)
        pdf_path = os.path.abspath("data/resumes/Dinesh_Kumar_S_2025.pdf")  # dynamic in real code

        # Start HTML UI (dark terminal theme)
        html_content = f"""
        <html>
        <head>
            <title>Resume Optimizer - {role}</title>
            <style>
                body {{
                    background-color: #000;
                    color: #fff;
                    font-family: 'Courier New', monospace;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    height: 100vh;
                }}
                .pdf-viewer {{
                    flex: 1;
                    border-right: 2px solid #333;
                    background: #111;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                }}
                iframe {{
                    width: 90%;
                    height: 90%;
                    border: 1px solid #666;
                    border-radius: 8px;
                    background-color: #000;
                }}
                .editor {{
                    flex: 1;
                    background-color: #0a0a0a;
                    padding: 20px;
                    display: flex;
                    flex-direction: column;
                }}
                h1 {{
                    color: #fff;
                    font-size: 18px;
                    margin-bottom: 10px;
                    border-bottom: 1px solid #333;
                }}
                textarea {{
                    flex: 1;
                    background-color: #000;
                    color: #00ffcc;
                    border: 1px solid #444;
                    border-radius: 8px;
                    padding: 10px;
                    resize: none;
                    font-size: 14px;
                    line-height: 1.5;
                    font-family: 'Courier New', monospace;
                    overflow-y: auto;
                    box-shadow: inset 0 0 10px #333;
                }}
            </style>
        </head>
        <body>
            <div class="pdf-viewer">
                <h1>📄 Original Resume</h1>
                <iframe src="file:///{pdf_path}" title="PDF Preview"></iframe>
            </div>
            <div class="editor">
                <h1>🧠 Optimized Resume for {role}</h1>
                <textarea id="editor" readonly>Initializing AI Resume Optimizer...</textarea>
            </div>
            <script>
                let textArea = document.getElementById('editor');
                let idx = 0;
                let text = "";
            </script>
        </body>
        </html>
        """

        output_html = os.path.join(os.getcwd(), "resume_optimizer_ui.html")
        with open(output_html, "w", encoding="utf-8") as f:
            f.write(html_content)

        console.print(f"\n🧠 [green]Opening Resume Optimizer Canvas...[/green]")
        os.startfile(output_html)

        # Start AI generation (simulate live writing)
        console.print(f"✔ Optimizing resume for [cyan]{role}[/cyan] ...\n")
        optimized_text = self.optimizer.llm.generate(
            f"Optimize this resume for the role of {role}:\n\n{self.current_resume_text}"
        )

        # Append generated text dynamically
        with open(output_html, "a", encoding="utf-8") as f:
            f.write(f"<script>text = `{optimized_text}`;\n"
                    "function typeWriter() {\n"
                    "  if (idx < text.length) {\n"
                    "    textArea.value += text.charAt(idx);\n"
                    "    idx++;\n"
                    "    setTimeout(typeWriter, 10);\n"
                    "  }\n"
                    "}\n"
                    "typeWriter();</script></body></html>")

        console.print(f"✅ [green]Optimization completed and displayed on canvas.[/green]")

    # 🧾 Summarize Resume
    def summarize_resume(self):
        if not self.current_resume_text:
            console.print("[red]⚠️ Please load a resume first.[/red]")
            return

        console.print("\n🧾 [cyan]Analyzing resume summary...[/cyan]")
        console.print(" ✔ Thinking like an expert recruiter...")
        time.sleep(0.5)
        summary = self.rag.query("Summarize the loaded resume (key strengths, education, and roles).")

        console.print("\n✨ [green]Summary Generated:[/green]\n")
        self.stream_text(summary)

    # 🧭 Help
    def print_help(self):
        console.print(
            "\n[bold cyan]Available Commands[/bold cyan]\n"
            "[yellow]help[/yellow]                         Show help menu\n"
            "[yellow]load <path>[/yellow]                  Load and embed a resume\n"
            "[yellow]summarize[/yellow]                    Summarize loaded resume\n"
            "[yellow]score <role>[/yellow]                 ATS score against job description\n"
            "[yellow]optimize <role>[/yellow]              Optimize and export resume\n"
            "[yellow]jobs <query>[/yellow]                 Search LinkedIn (demo)\n"
            "[yellow]exit[/yellow]                         Quit\n"
        )

    # 🚀 Start Chat Session
    def start_chat(self):
        # show_banner()
        # console.print("\n🤖 [bold magenta]Resumini is ready![/bold magenta] Type [yellow]'help'[/yellow] or [yellow]'exit'[/yellow].\n")

        while True:
            try:
                raw = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n👋 Exiting Resumini.")
                break

            if not raw:
                continue

            parts = raw.split()
            cmd = parts[0].lower()

            if cmd == "exit":
                console.print("👋 [cyan]Goodbye! Have a great day![/cyan]")
                break

            elif cmd == "help":
                self.print_help()

            elif cmd == "load":
                if len(parts) < 2:
                    console.print("[red]⚠️ Usage:[/red] load <path>")
                    continue
                self.load_resume(" ".join(parts[1:]))

            elif cmd == "summarize":
                self.summarize_resume()

            elif cmd in ["score", "ats", "ats_score"]:
                role = " ".join(parts[1:]) if len(parts) > 1 else input("🎯 Target role: ")

                if not self.current_resume_text:
                    console.print("[red]⚠️ Please load a resume first.[/red]")
                    continue

                console.print("\n ✔ [cyan] Thinking... analyzing context...[/cyan]")
                time.sleep(1)
                console.print(" ✔ [cyan] Generating response...[/cyan]\n")
                time.sleep(0.8)

                score, ai_response = self.ats.analyze(self.current_resume_text, role)

                # Handle missing AI response gracefully
                if not ai_response or not ai_response.strip():
                    ai_response = "AI model not available or failed to generate analysis. Please check your API key or internet connection."

                report = self.generate_ats_report()
                self.display_ats_report(report, ai_text=ai_response, role=role, ai_score=score)

            # elif cmd == "optimize":
            #     import re, os, sys, io, base64

            #     if not self.current_resume_text:
            #         console.print("[red]⚠️ Please load a resume first.[/red]")
            #         continue

            #     # 🎯 Target role
            #     role = " ".join(parts[1:]) if len(parts) > 1 else input("🎯 Target role: ")

            #     # 👤 Candidate name
            #     match = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", self.current_resume_text)
            #     candidate_name = match.group(1).strip() if match else input("👤 Candidate name not found. Enter full name: ")

            #     console.print(f"\n🧠 [cyan]Opening Resume Optimizer Canvas...[/cyan]")
            #     time.sleep(0.6)
            #     console.print(f"✔ Optimizing resume for [bold green]{role}[/bold green] ({candidate_name})...\n")

            #     # Capture stdout during LLM call so streaming prints do not pollute terminal or block flow
            #     old_stdout = sys.stdout
            #     sys_stdout_buffer = io.StringIO()
            #     sys.stdout = sys_stdout_buffer

            #     try:
            #         prompt = f"""
            # You are an AI Resume Optimization Assistant.
            # Please rewrite the resume below to be ATS friendly and tailored for the role: {role}.
            # Return only the optimized resume (no explanations).

            # Resume:
            # --------------------
            # {self.current_resume_text}
            # --------------------
            # """
            #         optimized_text = self.optimizer.llm.generate(prompt)
            #     except Exception as e:
            #         optimized_text = f"⚠️ AI optimization failed: {e}"
            #     finally:
            #         # restore stdout
            #         sys.stdout = old_stdout

            #     # If optimized_text is None or empty, check buffer (in case the LLM printed but didn't return)
            #     if (not optimized_text or str(optimized_text).strip() == ""):
            #         printed = sys_stdout_buffer.getvalue().strip()
            #         if printed:
            #             # Try to extract final textual content from printed stream
            #             optimized_text = printed

            #     optimized_text = str(optimized_text).strip()

            #     # Prepare PDF embedding (base64) if the resume path exists
            #     pdf_html = "<p style='color:#888;'>⚠️ No resume PDF loaded.</p>"
            #     pdf_path = getattr(self, "loaded_resume_path", None)
            #     if pdf_path and os.path.exists(pdf_path):
            #         try:
            #             with open(pdf_path, "rb") as f:
            #                 pdf_data = f.read()
            #             pdf_base64 = base64.b64encode(pdf_data).decode("utf-8")
            #             pdf_html = f"""
            #             <embed src="data:application/pdf;base64,{pdf_base64}" type="application/pdf"
            #                 width="100%" height="90%"
            #                 style="border:1px solid #444; border-radius:8px; background:#111;">
            #             """
            #         except Exception as e:
            #             pdf_html = f"<p style='color:red;'>Error loading PDF: {e}</p>"

            #     # Encode optimized_text safely to inject into HTML and avoid JS issues
            #     encoded_text = base64.b64encode(optimized_text.encode("utf-8")).decode("utf-8")

            #     output_html = os.path.join(os.getcwd(), "resume_optimizer_canva.html")
            #     html_content = f"""
            #     <!doctype html>
            #     <html>
            #     <head>
            #     <meta charset="utf-8" />
            #     <title>Resume Optimizer Canvas</title>
            #     <style>
            #         body {{
            #         background-color: #000;
            #         color: #fff;
            #         font-family: 'Courier New', monospace;
            #         margin: 0;
            #         padding: 0;
            #         display: flex;
            #         height: 100vh;
            #         overflow: hidden;
            #         }}
            #         .left, .right {{ flex: 1; padding: 20px; box-sizing: border-box; }}
            #         .left {{ border-right: 1px solid #333; background-color: #0d0d0d; overflow: auto; }}
            #         .right {{ background-color: #000; display: flex; flex-direction: column; overflow: hidden; }}
            #         h1 {{ text-align: center; color: #fff; font-size: 20px; text-decoration: underline; margin: 6px 0 12px; }}
            #         embed {{ width:100%; height: calc(100vh - 120px); border-radius:8px; border:1px solid #444; }}
            #         textarea {{
            #         width: 100%;
            #         height: calc(100vh - 120px);
            #         background-color: #000;
            #         color: #00ffcc;
            #         font-family: 'Courier New', monospace;
            #         font-size: 14px;
            #         border: 2px solid #0ff;
            #         border-radius: 10px;
            #         padding: 10px;
            #         resize: none;
            #         box-shadow: 0 0 15px #0ff;
            #         overflow: auto;
            #         }}
            #         .status {{ color: #00ffff; font-size: 14px; margin-bottom: 8px; text-shadow: 0 0 5px #0ff; }}
            #     </style>
            #     </head>
            #     <body>
            #     <div class="left">
            #         <h1>📄 Original Resume</h1>
            #         {pdf_html}
            #     </div>

            #     <div class="right">
            #         <h1>🧠 Optimized Resume for {role}</h1>
            #         <div class="status">✅ AI optimization ready — loaded in editor below</div>
            #         <textarea id="editor" readonly></textarea>
            #     </div>

            #     <script>
            #         // decode base64 optimized text and inject into editor
            #         (function() {{
            #         const encoded = "{encoded_text}";
            #         let decoded = "";
            #         try {{
            #             decoded = atob(encoded);
            #         }} catch (e) {{
            #             decoded = "Error decoding optimized text.";
            #         }}
            #         const editor = document.getElementById("editor");
            #         editor.value = decoded;
            #         // auto-scroll caret to end
            #         editor.scrollTop = editor.scrollHeight;
            #         }})();
            #     </script>
            #     </body>
            #     </html>
            #     """

            #     with open(output_html, "w", encoding="utf-8") as f:
            #         f.write(html_content)

            #     console.print("✅ [green]Optimization completed — Canva view ready![/green]")
            #     # open the file (platform default)
            #     try:
            #         os.startfile(output_html)
            #     except Exception:
            #         # fallback to webbrowser if startfile not available (Linux/mac)
            #         import webbrowser
            #         webbrowser.open(f"file://{output_html}")
            # elif cmd == "optimize":
                # import re, os, sys, io, base64, html

                # if not self.current_resume_text:
                #     console.print("[red]⚠️ Please load a resume first.[/red]")
                #     continue

                # # 🎯 Target role
                # role = " ".join(parts[1:]) if len(parts) > 1 else input("🎯 Target role: ")

                # # 👤 Candidate name
                # match = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", self.current_resume_text)
                # candidate_name = match.group(1).strip() if match else input("👤 Candidate name not found. Enter full name: ")

                # console.print(f"\n🧠 [cyan]Opening LaTeX Resume Optimizer Canvas...[/cyan]")
                # time.sleep(0.5)
                # console.print(f"✔ Optimizing resume for [bold green]{role}[/bold green] ({candidate_name})...\n")

                # # Capture stdout during LLM generation
                # old_stdout = sys.stdout
                # sys_stdout_buffer = io.StringIO()
                # sys.stdout = sys_stdout_buffer

                # try:
                #     prompt = f"""
                #     You are an AI Resume Optimization Assistant.
                #     Rewrite the following resume as a professional LaTeX resume document
                #     (use modern article formatting, minimal styling, and consistent spacing).
                #     The resume should be ATS-friendly, well-structured, and tailored for the role: {role}.
                #     Output ONLY the LaTeX code (no explanations or markdown).

                #     Resume:
                #     --------------------
                #     {self.current_resume_text}
                #     --------------------
                #     """
                #     optimized_text = self.optimizer.llm.generate(prompt)
                # except Exception as e:
                #     optimized_text = f"⚠️ AI optimization failed: {e}"
                # finally:
                #     sys.stdout = old_stdout

                # if (not optimized_text or str(optimized_text).strip() == ""):
                #     printed = sys_stdout_buffer.getvalue().strip()
                #     if printed:
                #         optimized_text = printed
                # optimized_text = str(optimized_text).strip()

                # # 🧾 Load PDF preview
                # pdf_html = "<p style='color:#888;'>⚠️ No resume PDF loaded.</p>"
                # pdf_path = getattr(self, "loaded_resume_path", None)
                # if pdf_path and os.path.exists(pdf_path):
                #     try:
                #         with open(pdf_path, "rb") as f:
                #             pdf_data = f.read()
                #         pdf_base64 = base64.b64encode(pdf_data).decode("utf-8")
                #         pdf_html = f"""
                #         <embed src="data:application/pdf;base64,{pdf_base64}" type="application/pdf"
                #             width="100%" height="90%"
                #             style="border:1px solid #444; border-radius:8px; background:#111;">
                #         """
                #     except Exception as e:
                #         pdf_html = f"<p style='color:red;'>Error loading PDF: {e}</p>"

                # # Encode LaTeX text safely
                # encoded_text = base64.b64encode(optimized_text.encode("utf-8")).decode("utf-8")

                # output_html = os.path.join(os.getcwd(), "resume_optimizer_canva.html")
                # html_content = f"""
                # <!doctype html>
                # <html>
                # <head>
                # <meta charset="utf-8" />
                # <title>LaTeX Resume Optimizer Canvas</title>
                # <style>
                #     body {{
                #         background-color: #000;
                #         color: #fff;
                #         font-family: 'Courier New', monospace;
                #         margin: 0;
                #         padding: 0;
                #         display: flex;
                #         height: 100vh;
                #         overflow: hidden;
                #     }}
                #     .left, .right {{ flex: 1; padding: 20px; box-sizing: border-box; }}
                #     .left {{ border-right: 1px solid #333; background-color: #0d0d0d; overflow: auto; }}
                #     .right {{ background-color: #000; display: flex; flex-direction: column; overflow: hidden; }}
                #     h1 {{ text-align: center; color: #fff; font-size: 20px; text-decoration: underline; margin: 6px 0 12px; }}
                #     embed {{ width:100%; height: calc(100vh - 120px); border-radius:8px; border:1px solid #444; }}
                #     pre {{
                #         width: 100%;
                #         height: calc(100vh - 120px);
                #         background-color: #000;
                #         color: #00ffcc;
                #         font-family: 'Courier New', monospace;
                #         font-size: 13px;
                #         border: 2px solid #0ff;
                #         border-radius: 10px;
                #         padding: 10px;
                #         overflow: auto;
                #         box-shadow: 0 0 15px #0ff;
                #         white-space: pre-wrap;
                #     }}
                #     .status {{ color: #00ffff; font-size: 14px; margin-bottom: 8px; text-shadow: 0 0 5px #0ff; }}
                # </style>
                # </head>
                # <body>
                # <div class="left">
                #     <h1>📄 Original Resume</h1>
                #     {pdf_html}
                # </div>

                # <div class="right">
                #     <h1>🧠 AI-Optimized LaTeX Resume for {role}</h1>
                #     <div class="status">✅ AI-generated LaTeX resume below:</div>
                #     <pre id="latex-viewer">Loading...</pre>
                # </div>

                # <script>
                #     (function() {{
                #         const encoded = "{encoded_text}";
                #         let decoded = "";
                #         try {{
                #             decoded = atob(encoded);
                #         }} catch (e) {{
                #             decoded = "Error decoding LaTeX resume.";
                #         }}
                #         const pre = document.getElementById("latex-viewer");
                #         pre.textContent = decoded;
                #         pre.scrollTop = pre.scrollHeight;
                #     }})();
                # </script>
                # </body>
                # </html>
                # """

                # with open(output_html, "w", encoding="utf-8") as f:
                #     f.write(html_content)

                # console.print("✅ [green]LaTeX resume optimization completed — Canva view ready![/green]")
                # try:
                #     os.startfile(output_html)
                # except Exception:
                #     import webbrowser
                #     webbrowser.open(f"file://{output_html}")

            elif cmd == "optimize":
                import re, os, sys, io, base64, subprocess, tempfile, requests, shutil, webbrowser

                if not self.current_resume_text:
                    console.print("[red]⚠️ Please load a resume first.[/red]")
                    continue

                # 🎯 Target role
                role = " ".join(parts[1:]) if len(parts) > 1 else input("🎯 Target role: ")

                # 👤 Candidate name
                match = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", self.current_resume_text)
                candidate_name = match.group(1).strip() if match else input("👤 Candidate name not found. Enter full name: ")

                console.print(f"\n🧠 [cyan]Opening Resume Optimizer Canvas (LaTeX compiled)...[/cyan]")
                time.sleep(0.6)
                console.print(f"✔ Optimizing resume for [bold green]{role}[/bold green] ({candidate_name})...\n")

                # Capture stdout safely
                old_stdout = sys.stdout
                sys_stdout_buffer = io.StringIO()
                sys.stdout = sys_stdout_buffer

                try:
                    prompt = f"""
                    You are an AI Resume Optimization Agent.
                    Convert the resume below into clean, modern LaTeX format (single-page layout, 11pt font).
                    add divider line for each section
                    Use \\documentclass[11pt]{{article}}, \\usepackage[utf8]{{inputenc}}, \\usepackage[T1]{{fontenc}},
                    \\usepackage{{geometry}}, \\usepackage{{enumitem}}, \\usepackage{{hyperref}}, and \\pagestyle{{empty}}.
                    The layout must look like a professional single-page resume (no extra page).
                    Compress vertical spaces using \\setlength commands.
                    Do NOT include emojis or markdown.
                    Tailor the text to the target role: {role}.
                    Output *only* valid LaTeX code ready to compile.

                    Resume:
                    --------------------
                    {self.current_resume_text}
                    --------------------
                    """
                    optimized_latex = self.optimizer.llm.generate(prompt)
                except Exception as e:
                    optimized_latex = f"⚠️ AI optimization failed: {e}"
                finally:
                    sys.stdout = old_stdout

                # Backup output if empty
                if (not optimized_latex or str(optimized_latex).strip() == ""):
                    printed = sys_stdout_buffer.getvalue().strip()
                    if printed:
                        optimized_latex = printed

                optimized_latex = str(optimized_latex).strip()
                optimized_latex = optimized_latex.encode("utf-8", "ignore").decode("utf-8")

                # 🧩 Force a correct preamble (compact + utf8)
                if "\\documentclass" not in optimized_latex:
                    optimized_latex = f"""
            \\documentclass[11pt]{{article}}
            \\usepackage[utf8]{{inputenc}}
            \\usepackage[T1]{{fontenc}}
            \\usepackage{{geometry}}
            \\usepackage{{enumitem}}
            \\usepackage{{hyperref}}
            \\geometry{{margin=0.75in}}
            \\setlength{{\\parindent}}{{0pt}}
            \\setlength{{\\parskip}}{{4pt}}
            \\setlist[itemize]{{leftmargin=*, itemsep=2pt, topsep=2pt}}
            \\pagestyle{{empty}}
            \\begin{{document}}
            {optimized_latex}
            \\end{{document}}
            """

                # 📂 Save LaTeX + Compile
                temp_dir = os.path.join(os.getcwd(), "optimized_resume_latex")
                os.makedirs(temp_dir, exist_ok=True)
                tex_path = os.path.join(temp_dir, "optimized_resume.tex")
                pdf_path = os.path.join(temp_dir, "optimized_resume.pdf")

                with open(tex_path, "w", encoding="utf-8") as f:
                    f.write(optimized_latex)

                console.print("⚙️ [yellow]Compiling LaTeX resume...[/yellow]")
                compiled_success = False

                try:
                    if shutil.which("pdflatex"):
                        subprocess.run(
                            ["pdflatex", "-interaction=nonstopmode", "-output-directory", temp_dir, tex_path],
                            check=True, capture_output=True, text=True
                        )
                        compiled_success = True
                        console.print("✅ [green]Local LaTeX compilation successful![/green]")
                    else:
                        raise FileNotFoundError("pdflatex not found")
                except Exception:
                    console.print("[yellow]⚠️ Local LaTeX not available — trying online compiler...[/yellow]")
                    try:
                        api_url = "https://latex.ytotech.com/builds/sync"
                        with open(tex_path, "rb") as f:
                            response = requests.post(api_url, files={"file": f})
                        if response.ok and response.headers.get("Content-Type", "").startswith("application/pdf"):
                            with open(pdf_path, "wb") as f:
                                f.write(response.content)
                            compiled_success = True
                            console.print("✅ [green]Online LaTeX compilation successful![/green]")
                        else:
                            raise RuntimeError(f"Online LaTeX compile failed: {response.text[:400]}")
                    except Exception as e2:
                        console.print(f"[red]❌ LaTeX compilation failed:[/red] {e2}")
                        pdf_path = None

                # Original Resume
                left_html = "<p style='color:#888;'>⚠️ Original resume not loaded.</p>"
                orig_pdf_path = getattr(self, "loaded_resume_path", None)
                if orig_pdf_path and os.path.exists(orig_pdf_path):
                    with open(orig_pdf_path, "rb") as f:
                        left64 = base64.b64encode(f.read()).decode("utf-8")
                        left_html = f"""<embed src="data:application/pdf;base64,{left64}" type="application/pdf"
                        width="100%" height="90%" style="border:1px solid #444; border-radius:8px;">"""

                # Optimized Resume
                right_html = "<p style='color:red;'>⚠️ No compiled PDF available.</p>"
                if compiled_success and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        right64 = base64.b64encode(f.read()).decode("utf-8")
                        right_html = f"""<embed src="data:application/pdf;base64,{right64}" type="application/pdf"
                        width="100%" height="90%" style="border:2px solid #0ff; border-radius:8px;">"""

                # Dual view HTML
                output_html = os.path.join(os.getcwd(), "resume_optimizer_canva.html")
                html = f"""
                <!doctype html><html><head><meta charset="utf-8" />
                <title>Resume Optimizer Canvas</title>
                <style>
                    body {{ background:#000; color:#fff; display:flex; height:100vh; margin:0; font-family:'Courier New'; }}
                    .left,.right {{ flex:1; padding:20px; box-sizing:border-box; }}
                    .left {{ background:#0d0d0d; border-right:1px solid #333; }}
                    .right {{ background:#000; }}
                    h1 {{ text-align:center; text-decoration:underline; color:#fff; font-size:20px; margin:8px 0 12px; }}
                </style></head>
                <body>
                    <div class="left"><h1>📄 Original Resume</h1>{left_html}</div>
                    <div class="right"><h1>🧠 AI-Optimized Resume</h1>{right_html}</div>
                </body></html>
                """
                with open(output_html, "w", encoding="utf-8") as f:
                    f.write(html)

                console.print("✅ [green]Compiled LaTeX resume ready — opening view...[/green]")
                try:
                    os.startfile(output_html)
                except Exception:
                    webbrowser.open(f"file://{output_html}")

    
            else:
                casual = ["hi", "hello", "hey", "thanks", "thank you"]
                if any(k in raw.lower() for k in casual):
                    system_prompt = (
                        '''You are Resumini, an intelligent AI Resume Summarization Agent that produces professional single-paragraph summaries suitable for recruiters and hiring systems.
                        Do not use markdown, lists, emojis, or decorative symbols.

                        Task:
                        Analyze the resume below and generate a single, coherent, professional paragraph summarizing the candidate’s overall profile.

                        Guidelines:
                        - Do not use markdown, emojis, or decorative formatting.
                        - Detect and include the candidate’s full name if mentioned.
                        - Mention total experience duration (if inferable), current or most recent role, and area of expertise.
                        - Highlight 4–6 most relevant skills, tools, or technologies naturally within the sentence.
                        - Mention educational background or domain focus if applicable.
                        - Avoid repetitive or filler words like “hardworking” or “motivated.”
                        - Keep tone objective, factual, and recruiter-friendly.
                        - Output should be a single paragraph of 100–130 words maximum.
                        - Do not use bullet points, numbered lists, or formatting symbols.
                        - The summary must read like a natural executive summary written by a hiring analyst.

                        Output Format (plain text only):

                        ==========================
                        CANDIDATE SUMMARY REPORT
                        ==========================
                        Candidate Name: <Extracted name or "Name not found">
                        Summary:
                        <One professional paragraph summarizing the resume content in fluent,seven words in a line, connected sentences.>
                        =========================='''
                    )
                    prompt = f"{system_prompt}\n\nUser: {raw}\nResumini:"
                    console.print(" ✔ Generating thoughtful response...\n")
                    response = self.llm.generate(prompt)
                    self.stream_text(response)
                else:
                    if not hasattr(self, "rag"):
                        console.print("[red]⚠️ Please load a resume first.[/red]")
                        continue
                    console.print(" ✔ Thinking... analyzing context...\n")
                    answer = self.rag.query(raw)
                    self.stream_text(answer)
