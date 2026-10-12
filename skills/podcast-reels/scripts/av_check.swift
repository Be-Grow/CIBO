// Confere um MP4 pelo AVFoundation (o motor do QuickTime, do Finder e do iPhone), não só pelo
// ffmpeg: um arquivo pode decodificar no ffmpeg e travar no QuickTime (parâmetros do H.264 que
// mudam no meio, emenda mal feita). Uso: av_check ARQ [t1 t2 ...] -> uma linha JSON por arquivo.
// Lê duração, se é reproduzível e gera um quadro em cada tempo pedido (padrão: 0,5 s, meio, fim).
import Foundation
import AVFoundation

let args = Array(CommandLine.arguments.dropFirst())
guard let path = args.first else { print("uso: av_check ARQ [tempos...]"); exit(2) }
let url = URL(fileURLWithPath: path)
let asset = AVURLAsset(url: url)
let sem = DispatchSemaphore(value: 0)
var out: [String: Any] = ["file": path]
Task {
    do {
        let (dur, playable) = try await asset.load(.duration, .isPlayable)
        let d = CMTimeGetSeconds(dur)
        out["duration"] = d
        out["playable"] = playable
        var times = args.dropFirst().compactMap { Double($0) }
        if times.isEmpty { times = [0.5, d / 2, max(0, d - 0.2)] }
        let gen = AVAssetImageGenerator(asset: asset)
        gen.requestedTimeToleranceBefore = .zero
        gen.requestedTimeToleranceAfter = .zero
        var bad: [Double] = []
        for t in times {
            do { _ = try await gen.image(at: CMTime(seconds: t, preferredTimescale: 600)) } catch { bad.append(t) }
        }
        out["frames_failed"] = bad
        out["ok"] = playable && bad.isEmpty
    } catch {
        out["ok"] = false
        out["error"] = "\(error)"
    }
    sem.signal()
}
sem.wait()
print(String(data: try! JSONSerialization.data(withJSONObject: out), encoding: .utf8)!)
exit((out["ok"] as? Bool) == true ? 0 : 1)
