import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="page-shell">
      <header className="site-header">
        <Link className="brand-lockup" href="/">
          <span className="brand-mark">N</span>
          <span className="brand-text">
            <strong>NeuraAI</strong>
            <span>Marketing operating system</span>
          </span>
        </Link>
        <nav className="nav-row">
          <Link className="button-ghost button-sm" href="/login">Войти</Link>
          <Link className="button-primary button-sm" href="/register">Создать аккаунт</Link>
        </nav>
      </header>

      <section className="hero-section">
        <div className="hero-copy">
          <span className="eyebrow">NeuraAI</span>
          <h1>Маркетинг и контент под управлением ИИ.</h1>
          <p className="lead">
            Создавай проекты, генерируй стратегию, планируй контент и публикуй
            в соцсети — всё в одном интерфейсе на базе искусственного интеллекта.
          </p>
          <div className="action-row">
            <Link className="button-primary" href="/register">Начать бесплатно</Link>
            <Link className="button-ghost" href="/login">Уже есть аккаунт</Link>
          </div>
          <div className="hero-stats">
            <article className="hero-stat">
              <strong>86%</strong>
              <span>Сокращение времени на стратегию</span>
            </article>
            <article className="hero-stat">
              <strong>3x</strong>
              <span>Больше контента за то же время</span>
            </article>
          </div>
        </div>
        <div className="hero-visual stagger">
          <article className="hero-card tilt-left">
            <span className="card-kicker">01 / Стратегия</span>
            <strong>AI анализирует бизнес и строит стратегию</strong>
            <p>Загрузи описание компании — ИИ проведёт анализ рынка, конкурентов и предложит контент-план.</p>
          </article>
          <article className="hero-card tilt-right">
            <span className="card-kicker">02 / Контент</span>
            <strong>Генерация и планирование публикаций</strong>
            <p>AI создаёт тексты постов, подбирает время публикации и формирует очередь на согласование.</p>
          </article>
          <article className="hero-card tilt-left">
            <span className="card-kicker">03 / Публикация</span>
            <strong>Telegram, VK, Instagram и другие каналы</strong>
            <p>Подключи соцсети, согласуй контент и публикуй автоматически по расписанию.</p>
          </article>
        </div>
      </section>

      <section className="feature-panel">
        <div className="section-heading">
          <span className="eyebrow">Платформа</span>
          <h2>Всё для управления маркетингом в одном месте</h2>
          <p className="lead" style={{ maxWidth: "70rem" }}>
            NeuraAI не просто генерирует текст. Он держит проектный контекст,
            помогает команде не терять статус работ и связывает аналитику с контентным циклом.
          </p>
        </div>
        <div className="feature-grid stagger">
          {[
            { num: "01", title: "Контекст бизнеса без хаоса", body: "Собирай данные по клиенту один раз и используй их во всех сценариях: стратегия, контент, публикации и аналитика." },
            { num: "02", title: "Стратегия и контент в одном цикле", body: "AI строит позиционирование, контентные опоры и рабочий календарь публикаций на недели вперёд." },
            { num: "03", title: "Контроль статусов по каждому проекту", body: "Видно, где ещё сбор данных, где уже активна стратегия, а где команда готова запускать публикации." },
            { num: "04", title: "Рабочее место для агентства и in-house", body: "Один интерфейс подходит и для внутренних маркетологов, и для команд, ведущих несколько клиентов одновременно." },
          ].map((item) => (
            <article className="feature-card" key={item.title}>
              <span className="card-num">{item.num}</span>
              <h3>{item.title}</h3>
              <p>{item.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="feature-panel" style={{ marginTop: 24 }}>
        <div className="section-heading">
          <span className="eyebrow">Цифры</span>
          <h2>Результаты, которые говорят сами за себя</h2>
        </div>
        <div className="stat-grid" style={{ marginTop: 8 }}>
          {[
            { value: "86%", label: "Сокращение времени на стратегию" },
            { value: "3x", label: "Больше контента за то же время" },
            { value: "12+", label: "Интегрированных соцсетей" },
            { value: "24/7", label: "AI работает без перерывов" },
          ].map((m) => (
            <article className="stat-card" key={m.label}>
              <span className="stat-value">{m.value}</span>
              <span className="stat-label">{m.label}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="cta-panel">
        <h2>Первый проект — бесплатно. Без карты.</h2>
        <p className="lead" style={{ margin: "0 auto 20px" }}>
          Регистрация занимает 30 секунд. После входа сразу попадаешь в рабочее пространство.
        </p>
        <div className="action-row" style={{ justifyContent: "center" }}>
          <Link className="button-primary" href="/register">Создать аккаунт</Link>
          <Link className="button-ghost" href="/login">Войти в систему</Link>
        </div>
      </section>

      <footer className="site-footer">
        <span>&copy; {new Date().getFullYear()} NeuraAI</span>
        <span>Marketing operating system</span>
      </footer>
    </main>
  );
}
