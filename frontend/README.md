# 🎬 Kuku Microdrama Promo Discovery — Next.js Dashboard

Modern web dashboard for promotional cutpoint discovery in serialized vertical microdramas (*I Married a Broken Soldier. He was a Duke*).

---

## 🔗 Quick Links & Key Deliverables

| Deliverable / Surface | Description | Link |
| :--- | :--- | :--- |
| **🌐 Next.js Dashboard** | Primary Production UI | **[http://localhost:3000](http://localhost:3000)** |
| **🎈 Streamlit App** | Legacy Streamlit UI | **[http://localhost:8501](http://localhost:8501)** |
| **🏆 Top 15 Ranked Promos** | Final listwise-ranked promotional cuts | [`../outputs/ranked.md`](../outputs/ranked.md) |
| **⚠️ Failure Modes & Audits** | 6 documented real failure modes & mitigations | [`../eval/failures.md`](../eval/failures.md) |
| **📖 System Architecture & Invariants** | System design and engineering runbook | [`../AGENTS.md`](../AGENTS.md) |
| **📝 Engineering Notes** | Assumptions, quota observations, and prompt logs | [`../NOTES.md`](../NOTES.md) |

---

## Getting Started

Run the production server:
```bash
npm install
npm run build
npx next start -p 3000
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the dashboard.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
