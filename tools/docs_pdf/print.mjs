// Print one HTML file to PDF with headless Chrome.
// Usage: node print.mjs <in.html> <out.pdf> <footer text>
import puppeteer from "puppeteer";
import { pathToFileURL } from "node:url";

const [input, output, footer] = process.argv.slice(2);
const browser = await puppeteer.launch({
  executablePath: process.env.CHROME_PATH,
  args: ["--no-sandbox"],
});
const page = await browser.newPage();
await page.goto(pathToFileURL(input).href, { waitUntil: "load" });
const esc = (s) => s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]);
await page.pdf({
  path: output,
  format: "Letter",
  margin: { top: "18mm", bottom: "18mm", left: "16mm", right: "16mm" },
  printBackground: true,
  displayHeaderFooter: true,
  headerTemplate: "<span></span>",
  footerTemplate:
    `<div style="font-size:7.5pt;color:#666;width:100%;padding:0 16mm;display:flex;justify-content:space-between;font-family:sans-serif">` +
    `<span>${esc(footer)}</span>` +
    `<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>`,
});
await browser.close();
