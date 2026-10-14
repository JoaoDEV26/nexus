import {
  useEffect,
  useState,
  createContext,
  useContext,
  type FormEvent,
  type ReactNode,
} from "react";
import { NavLink, Routes, Route, Navigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  api,
  renew,
  setToken,
  type Org,
  type Member,
  type Project,
  type Task,
  type Page,
  type Activity,
} from "./api";

const Context = createContext<{ org: Org; invalidate: () => Promise<void> }>(
  null!,
);
const labels: Record<string, string> = {
  TODO: "A fazer",
  IN_PROGRESS: "Em andamento",
  DONE: "Concluída",
  LOW: "Baixa",
  MEDIUM: "Média",
  HIGH: "Alta",
  ACTIVE: "Ativo",
  COMPLETED: "Concluído",
  ARCHIVED: "Arquivado",
  OWNER: "Proprietário",
  ADMIN: "Administrador",
  MANAGER: "Gestor",
  MEMBER: "Membro",
};
const name = (v: string) => labels[v] || v;
function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label>
      {label}
      {children}
    </label>
  );
}
function ErrorText({ error }: { error: unknown }) {
  return error ? (
    <p className="error" role="alert">
      {error instanceof Error ? error.message : String(error)}
    </p>
  ) : null;
}
function Pager({
  page,
  total,
  size = 20,
  change,
}: {
  page: number;
  total: number;
  size?: number;
  change: (n: number) => void;
}) {
  return (
    <div className="pager">
      <button disabled={page <= 1} onClick={() => change(page - 1)}>
        Anterior
      </button>
      <span>
        Página {page} · {total} registros
      </span>
      <button disabled={page * size >= total} onClick={() => change(page + 1)}>
        Próxima
      </button>
    </div>
  );
}
function useAction() {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  return {
    error,
    busy,
    run: async (fn: () => Promise<void>) => {
      setError("");
      setBusy(true);
      try {
        await fn();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Falha inesperada");
      } finally {
        setBusy(false);
      }
    },
  };
}
function Auth({ done }: { done: () => void }) {
  const [signup, setSignup] = useState(false);
  const action = useAction();
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const d = new FormData(e.currentTarget);
    await action.run(async () => {
      const credentials = {
        email: d.get("email"),
        password: d.get("password"),
      };
      if (signup)
        await api("/auth/register", "POST", {
          ...credentials,
          name: d.get("name"),
        });
      const r = await api<{ access_token: string }>(
        "/auth/login",
        "POST",
        credentials,
      );
      setToken(r.access_token);
      done();
    });
  }
  return (
    <main className="auth">
      <section className="authintro">
        <span className="eyebrow">NEXUS / GESTÃO DE EQUIPES</span>
        <h1>
          Trabalho organizado.
          <br />
          Próximos passos claros.
        </h1>
        <p>Projetos, responsáveis e prazos em um só lugar.</p>
        <small>Projeto de estudo · use dados fictícios</small>
      </section>
      <section className="authbox">
        <h2>{signup ? "Crie sua conta" : "Entre no Nexus"}</h2>
        <p>Seu espaço de trabalho começa aqui.</p>
        <form onSubmit={submit}>
          {signup && (
            <Field label="Nome">
              <input name="name" required maxLength={120} />
            </Field>
          )}
          <Field label="E-mail">
            <input name="email" type="email" autoComplete="email" required />
          </Field>
          <Field label="Senha">
            <input
              name="password"
              type="password"
              autoComplete={signup ? "new-password" : "current-password"}
              minLength={12}
              maxLength={128}
              required
            />
          </Field>
          <small>Mínimo de 12 caracteres.</small>
          <ErrorText error={action.error} />
          <button className="primary" disabled={action.busy}>
            {action.busy
              ? "Aguarde…"
              : signup
                ? "Cadastrar e entrar"
                : "Entrar"}
          </button>
        </form>
        <button className="link" onClick={() => setSignup(!signup)}>
          {signup ? "Já tenho uma conta" : "Criar conta"}
        </button>
      </section>
    </main>
  );
}
export default function App() {
  const [ready, setReady] = useState(false),
    [logged, setLogged] = useState(false);
  const qc = useQueryClient();
  useEffect(() => {
    renew().then((ok) => {
      setLogged(ok);
      setReady(true);
    });
    const expired = () => {
      setLogged(false);
      qc.clear();
    };
    window.addEventListener("session-ended", expired);
    return () => window.removeEventListener("session-ended", expired);
  }, [qc]);
  if (!ready) return <p className="loading">Verificando sessão…</p>;
  return logged ? (
    <Workspace
      logout={() => {
        setToken("");
        qc.clear();
        setLogged(false);
      }}
    />
  ) : (
    <Auth done={() => setLogged(true)} />
  );
}
function Workspace({ logout }: { logout: () => void }) {
  const qc = useQueryClient();
  const [id, setId] = useState("");
  const [creating, setCreating] = useState(false);
  const action = useAction();
  const q = useQuery({
    queryKey: ["organizations"],
    queryFn: () => api<Org[]>("/organizations"),
  });
  const org = q.data?.find((x) => x.id === id) || q.data?.[0];
  const invalidate = async () => {
    await qc.invalidateQueries();
  };
  async function create(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    await action.run(async () => {
      const item = await api<Org>("/organizations", "POST", {
        name: data.get("name"),
      });
      setId(item.id);
      setCreating(false);
      await invalidate();
    });
  }
  if (q.isPending) return <p className="loading">Carregando organizações…</p>;
  return (
    <div className="layout">
      <aside>
        <div className="brand">
          NEXUS<span>Workspace</span>
        </div>
        <Field label="Organização">
          <select
            aria-label="Organização"
            value={org?.id || ""}
            onChange={(e) => setId(e.target.value)}
          >
            {q.data?.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>
        </Field>
        <button className="neworg" onClick={() => setCreating(!creating)}>
          + Nova organização
        </button>
        <nav>
          {[
            ["/", "Visão geral"],
            ["/projects", "Projetos"],
            ["/tasks", "Tarefas"],
            ["/members", "Membros"],
            ["/activity", "Histórico"],
            ["/settings", "Configurações"],
          ].map(([url, label]) => (
            <NavLink end={url === "/"} key={url} to={url}>
              {label}
            </NavLink>
          ))}
        </nav>
        <button
          onClick={() =>
            action.run(async () => {
              await api("/auth/logout", "POST");
              logout();
            })
          }
        >
          Sair
        </button>
      </aside>
      <main className="content">
        <header>
          <span>ESPAÇO DE TRABALHO</span>
          <span>{org ? name(org.role) : "Bem-vindo"}</span>
        </header>
        <ErrorText error={q.error || action.error} />
        {(creating || !org) && (
          <section className="panel">
            <h1>Crie uma organização</h1>
            <p>Ela separa os projetos e membros da sua equipe.</p>
            <form className="inline" onSubmit={create}>
              <Field label="Nome da organização">
                <input
                  name="name"
                  required
                  maxLength={120}
                  placeholder="Aurora Studio"
                />
              </Field>
              <button className="primary" disabled={action.busy}>
                Criar organização
              </button>
            </form>
          </section>
        )}
        {org && (
          <Context.Provider value={{ org, invalidate }}>
            <div key={org.id}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/projects" element={<Projects />} />
                <Route path="/tasks" element={<Tasks />} />
                <Route path="/members" element={<Members />} />
                <Route path="/activity" element={<History />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </div>
          </Context.Provider>
        )}
      </main>
    </div>
  );
}
function useOrg() {
  const c = useContext(Context);
  return {
    ...c,
    base: `/organizations/${c.org.id}`,
    manage: c.org.role !== "MEMBER",
    admin: ["OWNER", "ADMIN"].includes(c.org.role),
  };
}
function Dashboard() {
  const { org, base } = useOrg();
  const [start, setStart] = useState(""),
    [end, setEnd] = useState("");
  const query = useQuery({
    queryKey: [org.id, "dashboard", start, end],
    queryFn: () =>
      api<Record<string, number | string>>(
        `${base}/dashboard?${new URLSearchParams({ ...(start ? { start } : {}), ...(end ? { end } : {}) })}`,
      ),
  });
  return (
    <>
      <div className="title">
        <div>
          <h1>Visão geral</h1>
          <p>Uma leitura clara do trabalho da equipe.</p>
        </div>
        <NavLink className="button primary" to="/tasks">
          Ver tarefas
        </NavLink>
      </div>
      <div className="filters">
        <Field label="Concluídas desde">
          <input
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </Field>
        <Field label="Até esta data sem incluí-la">
          <input
            type="date"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
          />
        </Field>
      </div>
      <ErrorText error={query.error} />
      {query.isPending ? (
        <p>Carregando indicadores…</p>
      ) : (
        query.data && (
          <>
            <div className="metrics">
              {[
                ["active_projects", "Projetos ativos"],
                ["pending_tasks", "Tarefas pendentes"],
                ["overdue_tasks", "Tarefas atrasadas"],
                ["completed_tasks", "Concluídas no período"],
              ].map(([key, title]) => (
                <section className="metric" key={key}>
                  <span>{title}</span>
                  <strong>{query.data[key]}</strong>
                </section>
              ))}
            </div>
            <section className="panel">
              <h2>Como ler estes números</h2>
              <p>
                Pendências e atrasos consideram tarefas não arquivadas de
                projetos ativos. Atraso é um prazo anterior à data de hoje.
              </p>
              <p>
                As conclusões consideram o período de {String(query.data.start)}{" "}
                até {String(query.data.end_exclusive)} sem incluir a última
                data. Fuso: {String(query.data.timezone)}.
              </p>
              <p>
                Reabrir uma tarefa retira sua conclusão do indicador. O
                histórico conserva a mudança.
              </p>
            </section>
          </>
        )
      )}
    </>
  );
}
function Projects() {
  const { org, base, manage, invalidate } = useOrg();
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<Project | null>(null);
  const action = useAction();
  const q = useQuery({
    queryKey: [org.id, "projects", page],
    queryFn: () => api<Page<Project>>(`${base}/projects?page_number=${page}`),
  });
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget,
      d = new FormData(form);
    await action.run(async () => {
      await api(
        editing ? `${base}/projects/${editing.id}` : `${base}/projects`,
        editing ? "PATCH" : "POST",
        {
          name: d.get("name"),
          description: d.get("description"),
          ...(editing ? { status: d.get("status") } : {}),
        },
      );
      setEditing(null);
      form.reset();
      await invalidate();
    });
  }
  return (
    <>
      <h1>Projetos</h1>
      <p>Organize entregas e acompanhe seu ciclo de vida.</p>
      {manage && (
        <section className="panel">
          <h2>{editing ? "Editar projeto" : "Novo projeto"}</h2>
          <form key={editing?.id || "new"} onSubmit={save}>
            <div className="formgrid">
              <Field label="Nome">
                <input
                  name="name"
                  defaultValue={editing?.name}
                  required
                  maxLength={120}
                />
              </Field>
              {editing && (
                <Field label="Status">
                  <select name="status" defaultValue={editing.status}>
                    {["ACTIVE", "COMPLETED", "ARCHIVED"].map((s) => (
                      <option key={s} value={s}>
                        {name(s)}
                      </option>
                    ))}
                  </select>
                </Field>
              )}
            </div>
            <Field label="Descrição">
              <textarea
                name="description"
                defaultValue={editing?.description}
                maxLength={5000}
              />
            </Field>
            <button className="primary" disabled={action.busy}>
              Salvar projeto
            </button>
            {editing && (
              <button type="button" onClick={() => setEditing(null)}>
                Cancelar
              </button>
            )}
          </form>
        </section>
      )}
      <ErrorText error={action.error || q.error} />
      {q.isPending ? (
        <p>Carregando…</p>
      ) : (
        <>
          <div className="cards">
            {q.data?.items.map((p) => (
              <article className="panel" key={p.id}>
                <span className="badge">{name(p.status)}</span>
                <h2>{p.name}</h2>
                <p className="prewrap">{p.description || "Sem descrição."}</p>
                {manage && (
                  <button onClick={() => setEditing(p)}>Editar projeto</button>
                )}
              </article>
            ))}
          </div>
          {q.data?.total === 0 && (
            <p className="empty">Nenhum projeto criado.</p>
          )}
          <Pager page={page} total={q.data?.total || 0} change={setPage} />
        </>
      )}
    </>
  );
}
function Tasks() {
  const { org, base, manage, invalidate } = useOrg();
  const [page, setPage] = useState(1),
    [status, setStatus] = useState(""),
    [priority, setPriority] = useState(""),
    [project, setProject] = useState(""),
    [assigned, setAssigned] = useState(""),
    [search, setSearch] = useState(""),
    [archived, setArchived] = useState(false);
  const [editing, setEditing] = useState<Task | null>(null),
    [detail, setDetail] = useState<Task | null>(null);
  const action = useAction();
  const projects = useQuery({
    queryKey: [org.id, "all-projects"],
    queryFn: () => allProjects(base),
  });
  const members = useQuery({
    queryKey: [org.id, "members"],
    queryFn: () => api<Member[]>(`${base}/members`),
  });
  const params = new URLSearchParams({
    page_number: String(page),
    q: search,
    archived: String(archived),
    ...(status ? { status } : {}),
    ...(priority ? { priority } : {}),
    ...(project ? { project_id: project } : {}),
    ...(assigned ? { assignee_id: assigned } : {}),
  });
  const q = useQuery({
    queryKey: [org.id, "tasks", params.toString()],
    queryFn: () => api<Page<Task>>(`${base}/tasks?${params}`),
  });
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = e.currentTarget,
      d = new FormData(f);
    await action.run(async () => {
      const body = {
        title: d.get("title"),
        description: d.get("description"),
        priority: d.get("priority"),
        assignee_id: d.get("assignee_id") || null,
        due_date: d.get("due_date") || null,
        ...(!editing ? { project_id: d.get("project_id") } : {}),
      };
      await api(
        editing ? `${base}/tasks/${editing.id}` : `${base}/tasks`,
        editing ? "PATCH" : "POST",
        body,
      );
      setEditing(null);
      f.reset();
      await invalidate();
    });
  }
  function filter(set: (x: string) => void, value: string) {
    set(value);
    setPage(1);
  }
  return (
    <>
      <h1>Tarefas</h1>
      <p>Uma tarefa, um responsável, um próximo passo.</p>
      {manage && (
        <section className="panel">
          <h2>{editing ? "Editar tarefa" : "Nova tarefa"}</h2>
          <form key={editing?.id || "new"} onSubmit={save}>
            <div className="formgrid">
              <Field label="Título">
                <input
                  name="title"
                  required
                  maxLength={120}
                  defaultValue={editing?.title}
                />
              </Field>
              {!editing && (
                <Field label="Projeto ativo">
                  <select name="project_id" required>
                    <option value="">Selecione</option>
                    {projects.data
                      ?.filter((p) => p.status === "ACTIVE")
                      .map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                  </select>
                </Field>
              )}
              <Field label="Responsável">
                <select
                  name="assignee_id"
                  defaultValue={editing?.assignee_id || ""}
                >
                  <option value="">Sem responsável</option>
                  {members.data?.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Prioridade">
                <select
                  name="priority"
                  defaultValue={editing?.priority || "MEDIUM"}
                >
                  {["LOW", "MEDIUM", "HIGH"].map((v) => (
                    <option key={v} value={v}>
                      {name(v)}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Prazo">
                <input
                  name="due_date"
                  type="date"
                  defaultValue={editing?.due_date || ""}
                />
              </Field>
            </div>
            <Field label="Descrição">
              <textarea
                name="description"
                maxLength={5000}
                defaultValue={editing?.description}
              />
            </Field>
            <button
              className="primary"
              disabled={
                action.busy ||
                !projects.data?.some((p) => p.status === "ACTIVE")
              }
            >
              Salvar tarefa
            </button>
            {editing && (
              <button type="button" onClick={() => setEditing(null)}>
                Cancelar
              </button>
            )}
          </form>
        </section>
      )}
      <div className="filters">
        <Field label="Buscar título">
          <input
            value={search}
            onChange={(e) => filter(setSearch, e.target.value)}
          />
        </Field>
        <Field label="Status">
          <select
            value={status}
            onChange={(e) => filter(setStatus, e.target.value)}
          >
            <option value="">Todos</option>
            {["TODO", "IN_PROGRESS", "DONE"].map((v) => (
              <option key={v} value={v}>
                {name(v)}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Prioridade">
          <select
            value={priority}
            onChange={(e) => filter(setPriority, e.target.value)}
          >
            <option value="">Todas</option>
            {["LOW", "MEDIUM", "HIGH"].map((v) => (
              <option key={v} value={v}>
                {name(v)}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Projeto">
          <select
            value={project}
            onChange={(e) => filter(setProject, e.target.value)}
          >
            <option value="">Todos</option>
            {projects.data?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Responsável">
          <select
            value={assigned}
            onChange={(e) => filter(setAssigned, e.target.value)}
          >
            <option value="">Todos</option>
            {members.data?.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </Field>
        <label className="check">
          <input
            type="checkbox"
            checked={archived}
            onChange={(e) => {
              setArchived(e.target.checked);
              setPage(1);
            }}
          />
          Arquivadas
        </label>
      </div>
      <ErrorText
        error={action.error || q.error || projects.error || members.error}
      />
      {q.isPending ? (
        <p>Carregando tarefas…</p>
      ) : (
        <>
          <div className="tasklist">
            {q.data?.items.map((t) => (
              <article className="taskrow" key={t.id}>
                <div>
                  <span className={"badge " + t.priority.toLowerCase()}>
                    {name(t.priority)}
                  </span>
                  <h3>{t.title}</h3>
                  <p>
                    {projects.data?.find((p) => p.id === t.project_id)?.name} ·{" "}
                    {members.data?.find((m) => m.id === t.assignee_id)?.name ||
                      "Sem responsável"}{" "}
                    · {t.due_date || "Sem prazo"}
                  </p>
                </div>
                <div className="actions">
                  <select
                    aria-label={`Status de ${t.title}`}
                    value={t.status}
                    disabled={
                      action.busy ||
                      t.archived ||
                      (!manage && t.assignee_id !== org.membership_id)
                    }
                    onChange={(e) =>
                      action.run(async () => {
                        await api(`${base}/tasks/${t.id}/status`, "PATCH", {
                          status: e.target.value,
                        });
                        await invalidate();
                      })
                    }
                  >
                    {["TODO", "IN_PROGRESS", "DONE"].map((v) => (
                      <option key={v} value={v}>
                        {name(v)}
                      </option>
                    ))}
                  </select>
                  <button onClick={() => setDetail(t)}>Detalhes</button>
                  {manage && (
                    <>
                      <button onClick={() => setEditing(t)}>Editar</button>
                      <button
                        disabled={action.busy}
                        onClick={() =>
                          action.run(async () => {
                            await api(`${base}/tasks/${t.id}`, "PATCH", {
                              archived: !t.archived,
                            });
                            await invalidate();
                          })
                        }
                      >
                        {t.archived ? "Restaurar" : "Arquivar"}
                      </button>
                    </>
                  )}
                </div>
              </article>
            ))}
          </div>
          {q.data?.total === 0 && (
            <p className="empty">Nenhuma tarefa para estes filtros.</p>
          )}
          <Pager page={page} total={q.data?.total || 0} change={setPage} />
        </>
      )}
      {detail && <TaskDetails task={detail} close={() => setDetail(null)} />}
    </>
  );
}
async function allProjects(base: string): Promise<Project[]> {
  let number = 1;
  const result: Project[] = [];
  while (true) {
    const p = await api<Page<Project>>(
      `${base}/projects?page_size=100&page_number=${number}`,
    );
    result.push(...p.items);
    if (result.length >= p.total) return result;
    number++;
  }
}
function TaskDetails({ task, close }: { task: Task; close: () => void }) {
  const { org, base, invalidate } = useOrg();
  const [page, setPage] = useState(1);
  const action = useAction();
  const q = useQuery({
    queryKey: [org.id, "comments", task.id, page],
    queryFn: () =>
      api<Page<{ id: string; body: string; created_at: string }>>(
        `${base}/tasks/${task.id}/comments?page_number=${page}`,
      ),
  });
  return (
    <section className="panel details" aria-label="Detalhes da tarefa">
      <button className="close" onClick={close}>
        Fechar detalhes
      </button>
      <h2>{task.title}</h2>
      <p className="prewrap">{task.description || "Sem descrição."}</p>
      <h3>Comentários</h3>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const f = e.currentTarget;
          const d = new FormData(f);
          action.run(async () => {
            await api(`${base}/tasks/${task.id}/comments`, "POST", {
              body: d.get("body"),
            });
            f.reset();
            setPage(1);
            await invalidate();
          });
        }}
      >
        <Field label="Novo comentário">
          <textarea name="body" required maxLength={2000} />
        </Field>
        <button className="primary" disabled={action.busy || task.archived}>
          Comentar
        </button>
      </form>
      <ErrorText error={action.error || q.error} />
      {q.isPending ? (
        <p>Carregando comentários…</p>
      ) : (
        q.data?.items.map((c) => (
          <article className="comment" key={c.id}>
            <small>{new Date(c.created_at).toLocaleString("pt-BR")}</small>
            <p className="prewrap">{c.body}</p>
          </article>
        ))
      )}
      {q.data?.total === 0 && <p>Sem comentários.</p>}
      <Pager page={page} total={q.data?.total || 0} change={setPage} />
      <History entity={task.id} />
    </section>
  );
}
function Members() {
  const { org, base, admin, invalidate } = useOrg();
  const action = useAction();
  const q = useQuery({
    queryKey: [org.id, "members"],
    queryFn: () => api<Member[]>(`${base}/members`),
  });
  const roles =
    org.role === "OWNER"
      ? ["ADMIN", "MANAGER", "MEMBER"]
      : ["MANAGER", "MEMBER"];
  return (
    <>
      <h1>Membros</h1>
      <p>O papel vale apenas para esta organização.</p>
      {admin && (
        <section className="panel">
          <h2>Adicionar uma conta existente</h2>
          <p>
            A pessoa precisa ter se cadastrado antes. Nenhum e-mail será
            enviado.
          </p>
          <form
            className="inline"
            onSubmit={(e) => {
              e.preventDefault();
              const f = e.currentTarget,
                d = new FormData(f);
              action.run(async () => {
                await api(`${base}/members`, "POST", {
                  email: d.get("email"),
                  role: d.get("role"),
                });
                f.reset();
                await invalidate();
              });
            }}
          >
            <Field label="E-mail">
              <input name="email" type="email" required />
            </Field>
            <Field label="Papel">
              <select name="role" defaultValue="MEMBER">
                {roles.map((r) => (
                  <option key={r} value={r}>
                    {name(r)}
                  </option>
                ))}
              </select>
            </Field>
            <button className="primary" disabled={action.busy}>
              Adicionar
            </button>
          </form>
        </section>
      )}
      <ErrorText error={action.error || q.error} />
      {q.isPending ? (
        <p>Carregando membros…</p>
      ) : (
        q.data?.map((m) => (
          <article className="taskrow" key={m.id}>
            <div>
              <h3>{m.name}</h3>
              <p>{m.email}</p>
            </div>
            <div className="actions">
              <span className="badge">{name(m.role)}</span>
              {admin &&
                m.role !== "OWNER" &&
                (org.role === "OWNER" || m.role !== "ADMIN") && (
                  <>
                    <select
                      aria-label={`Papel de ${m.name}`}
                      value={m.role}
                      disabled={action.busy}
                      onChange={(e) =>
                        action.run(async () => {
                          await api(`${base}/members/${m.id}`, "PATCH", {
                            role: e.target.value,
                          });
                          await invalidate();
                        })
                      }
                    >
                      {roles.map((r) => (
                        <option key={r} value={r}>
                          {name(r)}
                        </option>
                      ))}
                    </select>
                    <button
                      disabled={action.busy}
                      onClick={() => {
                        if (
                          window.confirm(
                            `Remover ${m.name}? As tarefas abertas ficarão sem responsável.`,
                          )
                        )
                          action.run(async () => {
                            await api(`${base}/members/${m.id}`, "DELETE");
                            await invalidate();
                          });
                      }}
                    >
                      Remover
                    </button>
                  </>
                )}
            </div>
          </article>
        ))
      )}
    </>
  );
}
function History({ entity }: { entity?: string }) {
  const { org, base } = useOrg();
  const [page, setPage] = useState(1);
  const q = useQuery({
    queryKey: [org.id, "activity", entity, page],
    queryFn: () =>
      api<Page<Activity>>(
        `${base}/activity?page_number=${page}${entity ? "&entity_id=" + entity : ""}`,
      ),
  });
  return (
    <>
      <h2>{entity ? "Histórico da tarefa" : "Histórico de atividades"}</h2>
      <p>Alterações registradas na organização.</p>
      <ErrorText error={q.error} />
      {q.isPending ? (
        <p>Carregando histórico…</p>
      ) : (
        q.data?.items.map((a) => (
          <article className="event" key={a.id}>
            <strong>{a.action}</strong>
            <small>{new Date(a.created_at).toLocaleString("pt-BR")}</small>
            {Object.keys(a.changes).length > 0 && (
              <pre>{JSON.stringify(a.changes, null, 2)}</pre>
            )}
          </article>
        ))
      )}
      {q.data?.total === 0 && <p>Sem atividades.</p>}
      <Pager page={page} total={q.data?.total || 0} change={setPage} />
    </>
  );
}
function Settings() {
  const { org, base, admin, invalidate } = useOrg();
  const action = useAction();
  return (
    <>
      <h1>Configurações</h1>
      <section className="panel">
        <h2>Organização</h2>
        <p>Fuso dos indicadores: America/Sao_Paulo.</p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const d = new FormData(e.currentTarget);
            action.run(async () => {
              await api(base, "PATCH", { name: d.get("name") });
              await invalidate();
            });
          }}
        >
          <Field label="Nome">
            <input
              name="name"
              required
              maxLength={120}
              defaultValue={org.name}
              disabled={!admin}
            />
          </Field>
          <button className="primary" disabled={!admin || action.busy}>
            Salvar nome
          </button>
        </form>
        <ErrorText error={action.error} />
      </section>
    </>
  );
}
