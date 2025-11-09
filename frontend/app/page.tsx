export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-zinc-50 via-white to-zinc-100 font-sans dark:from-black dark:via-zinc-950 dark:to-zinc-900">
      <main className="flex min-h-screen w-full max-w-5xl flex-col items-center justify-center px-8 py-16 sm:px-16">
        <div className="flex flex-col items-center gap-8 text-center">
          {/* Main Title */}
          <h1 className="text-6xl font-bold tracking-tight text-black dark:text-white sm:text-7xl md:text-8xl lg:text-9xl">
            ArtWatch
          </h1>

          {/* Subtitle */}
          <p className="max-w-2xl text-xl font-medium text-zinc-700 dark:text-zinc-300 sm:text-2xl md:text-3xl">
            Intelligent Artwork Monitoring & Protection
          </p>

          {/* Description */}
          <div className="mt-8 max-w-3xl space-y-6 text-lg leading-relaxed text-zinc-600 dark:text-zinc-400 sm:text-xl">
            <p>
              Welcome to <span className="font-semibold text-black dark:text-white">ArtWatch</span>,
              an advanced surveillance system that uses cutting-edge computer vision technology to
              monitor and protect artwork in real-time, to ensure a heist like the infamous Lourve heist never happens again.
            </p>
          </div>

          {/* Feature Highlights */}
          <div className="mt-12 grid w-full max-w-2xl grid-cols-1 gap-6 sm:grid-cols-3">
            <div className="rounded-lg border border-zinc-200 bg-white/50 p-6 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-900/50">
              <div className="mb-3 text-3xl">👁️</div>
              <h3 className="mb-2 font-semibold text-black dark:text-white">Real-Time Monitoring</h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                Continuous 24/7 surveillance of your artwork
              </p>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white/50 p-6 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-900/50">
              <div className="mb-3 text-3xl">🤖</div>
              <h3 className="mb-2 font-semibold text-black dark:text-white">AI-Powered Detection</h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                Advanced YOLO object detection for accurate alerts
              </p>
            </div>
            <div className="rounded-lg border border-zinc-200 bg-white/50 p-6 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-900/50">
              <div className="mb-3 text-3xl">🔔</div>
              <h3 className="mb-2 font-semibold text-black dark:text-white">Instant Alerts</h3>
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                Get notified immediately when threats are detected
              </p>
            </div>
          </div>

          {/* Description continued */}
          <div className="mt-8 max-w-3xl space-y-6 text-lg leading-relaxed text-zinc-600 dark:text-zinc-400 sm:text-xl">
            <p>
              Powered by <span className="font-semibold text-black dark:text-white">OpenCV</span> and
              <span className="font-semibold text-black dark:text-white"> YOLO</span>, our system
              continuously watches over your displayed artwork using a webcam, detecting any changes,
              movements, or potential vandalism with precision and speed.
            </p>
            <p className="pt-4 text-base font-medium text-zinc-800 dark:text-zinc-200 sm:text-lg">
              Get instant alerts the moment something happens. Your art deserves protection,
              and ArtWatch delivers.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
