// Nota de rosto para escolher capa, com o Vision da Apple (roda local, sem rede).
// uso: face_quality IMG1.jpg IMG2.jpg ...   ->  uma linha JSON por imagem
// campos: quality (0–1, "face capture quality": nitidez, expressão, olhos, pose),
// yaw/pitch/roll (graus; 0 = de frente para a câmera), eyes (abertura média dos olhos,
// altura/largura do contorno; < ~0.12 costuma ser olho fechado), area (fração do quadro),
// hand_up (mão com algum ponto acima do queixo: gesto que disputa com o rosto na capa).
import Foundation
import Vision
import AppKit

func eyeOpen(_ r: VNFaceLandmarkRegion2D?) -> Double? {
    guard let r = r, r.pointCount > 3 else { return nil }
    let p = r.normalizedPoints
    let xs = p.map { Double($0.x) }, ys = p.map { Double($0.y) }
    let w = (xs.max()! - xs.min()!), h = (ys.max()! - ys.min()!)
    return w > 0 ? h / w : nil
}

for path in CommandLine.arguments.dropFirst() {
    var out: [String: Any] = ["file": path]
    guard let img = NSImage(contentsOfFile: path),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        out["error"] = "imagem ilegível"
        print(String(data: try! JSONSerialization.data(withJSONObject: out), encoding: .utf8)!)
        continue
    }
    let q = VNDetectFaceCaptureQualityRequest()
    let l = VNDetectFaceLandmarksRequest()
    let hp = VNDetectHumanHandPoseRequest()
    hp.maximumHandCount = 2
    let h = VNImageRequestHandler(cgImage: cg, options: [:])
    do { try h.perform([q, l, hp]) } catch { out["error"] = "\(error)" }
    // rosto principal = o maior
    let faces = (q.results ?? []).sorted { $0.boundingBox.width * $0.boundingBox.height > $1.boundingBox.width * $1.boundingBox.height }
    if let f = faces.first {
        out["quality"] = f.faceCaptureQuality.map { Double($0) } ?? NSNull()
        out["yaw"] = f.yaw.map { $0.doubleValue * 180 / .pi } ?? NSNull()
        out["pitch"] = f.pitch.map { $0.doubleValue * 180 / .pi } ?? NSNull()
        out["roll"] = f.roll.map { $0.doubleValue * 180 / .pi } ?? NSNull()
        out["area"] = Double(f.boundingBox.width * f.boundingBox.height)
        out["cx"] = Double(f.boundingBox.midX)
        let lm = (l.results ?? []).sorted { $0.boundingBox.width > $1.boundingBox.width }.first?.landmarks
        let e = [eyeOpen(lm?.leftEye), eyeOpen(lm?.rightEye)].compactMap { $0 }
        out["eyes"] = e.isEmpty ? NSNull() : e.reduce(0, +) / Double(e.count)
        out["faces"] = faces.count
        // mão acima do queixo (coordenadas do Vision: origem embaixo, y cresce para cima)
        var up = false
        for hand in hp.results ?? [] {
            if let pts = try? hand.recognizedPoints(.all) {
                for (_, pt) in pts where pt.confidence > 0.3 && pt.location.y > f.boundingBox.minY { up = true }
            }
        }
        out["hand_up"] = up
    } else {
        out["faces"] = 0
    }
    print(String(data: try! JSONSerialization.data(withJSONObject: out), encoding: .utf8)!)
}
