export default async function handler(req, res) {
  const path = [].concat(req.query.path || []).join("/")
  const qs = req.url.includes("?") ? req.url.slice(req.url.indexOf("?")) : ""

  const upstream = await fetch(`${process.env.API_URL.replace(/\/+$/, "")}/${path}${qs}`, {
    method: req.method,
    headers: {
      "Content-Type": "application/json",
      "X-Api-Key": process.env.API_KEY,
      ...(req.headers.authorization && { Authorization: req.headers.authorization }),
    },
    body: ["GET", "HEAD"].includes(req.method) ? undefined : JSON.stringify(req.body),
  })

  res
    .status(upstream.status)
    .setHeader("Content-Type", upstream.headers.get("content-type") || "application/json")
    .send(await upstream.text())
}