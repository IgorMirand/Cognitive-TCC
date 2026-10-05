// Proxy: o navegador chama /api/<rota> e esta função repassa para a API real,
// adicionando o X-Api-Key no servidor (a chave nunca chega ao navegador).
// Variáveis necessárias na Vercel: API_URL e API_KEY (sem prefixo VITE_).

module.exports = async function handler(req, res) {
  const base = (process.env.API_URL || "").replace(/\/+$/, "")
  const faltando = []
  if (!base) faltando.push("API_URL")
  if (!process.env.API_KEY) faltando.push("API_KEY")
  if (faltando.length) {
    return res.status(500).json({ detail: `Proxy sem variáveis: ${faltando.join(", ")}` })
  }

  // req.query traz "path" (segmentos da rota) + os parâmetros de query reais
  const { path, ...query } = req.query
  const caminho = [].concat(path || []).join("/")

  const params = new URLSearchParams()
  for (const [k, v] of Object.entries(query)) {
    for (const item of [].concat(v)) params.append(k, item)
  }
  const qs = params.toString()
  const url = `${base}/${caminho}${qs ? `?${qs}` : ""}`

  const semCorpo = ["GET", "HEAD"].includes(req.method) || req.body === undefined
  const corpo = semCorpo
    ? undefined
    : typeof req.body === "string" ? req.body : JSON.stringify(req.body)

  try {
    const upstream = await fetch(url, {
      method: req.method,
      headers: {
        "Content-Type": "application/json",
        "X-Api-Key": process.env.API_KEY,
        ...(req.headers.authorization && { Authorization: req.headers.authorization }),
      },
      body: corpo,
    })

    res
      .status(upstream.status)
      .setHeader("Content-Type", upstream.headers.get("content-type") || "application/json")
      .send(await upstream.text())
  } catch {
    res.status(502).json({ detail: "Não foi possível contatar a API." })
  }
}