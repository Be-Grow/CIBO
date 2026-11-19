// OCR de quadros com o Vision do macOS (sem instalar nada).
// uso: swift ocr_quadros.swift q1.png q2.png ...   → uma linha JSON por texto achado:
// {"img":"q1.png","texto":"...","conf":0.9,"x":0.1,"y":0.4,"w":0.5,"h":0.05}   (y a partir do TOPO, 0–1)
import Foundation
import Vision
import AppKit

for path in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { continue }
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.recognitionLanguages = ["pt-BR", "en-US"]
    req.usesLanguageCorrection = false
    try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
    for o in req.results ?? [] {
        guard let c = o.topCandidates(1).first else { continue }
        let b = o.boundingBox
        let d: [String: Any] = ["img": path, "texto": c.string, "conf": Double(c.confidence),
                                "x": Double(b.minX), "y": Double(1 - b.maxY), "w": Double(b.width), "h": Double(b.height)]
        if let j = try? JSONSerialization.data(withJSONObject: d), let s = String(data: j, encoding: .utf8) { print(s) }
    }
}
