module.exports = async function handler(req, res) {
  const base = (process.env.API_URL || "").trim().replace(/\/+$/, "")
  const chave = (process.env.API_KEY || "").trim()
  const faltando = []
  if (!base) faltando.push("API_URL")
  if (!chave) faltando.push("API_KEY")
  if (faltando.length) {
    return res.status(500).json({ detail: `Proxy sem variáveis: ${faltando.join(", ")}` })
  }

  const original = new URL(req.url, "http://localhost")
  let caminho = [].concat(req.query.path || []).join("/")
  if (!caminho) caminho = original.pathname.replace(/^\/api\/?/, "")
  original.searchParams.delete("path")
  const qs = original.searchParams.toString()
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
        "X-Api-Key": chave,
        ...(req.headers.authorization && { Authorization: req.headers.authorization }),
      },
      body: corpo,
    })

    // DIAGNÓSTICO (remova depois)
    res.setHeader("x-proxy-target", url)
    res.setHeader("x-proxy-final", upstream.url)

    res
      .status(upstream.status)
      .setHeader("Content-Type", upstream.headers.get("content-type") || "application/json")
      .send(await upstream.text())
  } catch {
    res.status(502).json({ detail: "Não foi possível contatar a API." })
  }
}