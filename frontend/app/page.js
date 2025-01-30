import Navbar from "@/components/global/Navbar";
import Image from "next/image";
import Link from "next/link";
import image from "@/public/hero.png";
import { Book, Brain } from "lucide-react";

export default function Home() {
  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gradient-to-br from-white via-blue-50 to-orange-50">
        <main className="max-w-screen-xl mx-auto px-10 pt-8 pb-8 flex flex-col gap-y-6">
          <div className="grid lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-7">
              <div className="relative">
                <div className="absolute -left-4 -top-4 w-24 h-24 bg-primary/10 rounded-full blur-3xl"></div>
                <div className="absolute right-20 top-10 w-32 h-32 bg-secondary/10 rounded-full blur-3xl"></div>
                <h1 className="relative text-4xl md:text-5xl xl:text-6xl font-extrabold text-text-primary font-sans">
                  GenPlan: Solusi Penjadwalan Kampus Tanpa Konflik
                </h1>
              </div>
              <p className="text-text-secondary mt-6 text-lg font-sans">
                Optimalisasi jadwal perkuliahan menggunakan algoritma Genetic
                Algorithm dan Simulated Annealing untuk menciptakan jadwal yang
                efisien dan bebas dari tumpang tindih.
              </p>

              <div className="mt-8 flex space-x-4">
                <Link
                  href="/login"
                  className="bg-gradient-to-r from-primary to-primary/90 text-primary-foreground px-6 py-3 rounded-lg hover:from-primary/90 hover:to-primary transition-all duration-300 font-sans"
                >
                  Login
                </Link>
                <Link
                  href="/dokumentasi"
                  className="border border-border bg-white/50 backdrop-blur-sm text-text-primary px-6 py-3 rounded-lg hover:bg-white/80 transition-colors font-sans"
                >
                  Pelajari Lebih Lanjut
                </Link>
              </div>
            </div>
            <div className="hidden lg:block lg:col-span-5">
              <div className="">
                <Image
                  src={image}
                  alt="Ilustrasi GenPlan"
                  width={500}
                  height={500}
                  className="rounded-lg"
                />
              </div>
            </div>
          </div>

          <div className="mt-8">
            <h2 className="text-2xl font-bold text-text-primary mb-6 font-sans">
              Keunggulan GenPlan:
            </h2>
            <div className="space-y-8">
              {[
                {
                  icon: (
                    <svg
                      className="h-6 w-6"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 10V3L4 14h7v7l9-11h-7z"
                      />
                    </svg>
                  ),
                  title: "Optimalisasi Otomatis",
                  description:
                    "Menggunakan algoritma canggih untuk menghasilkan jadwal optimal secara otomatis",
                  bgClass: "bg-gradient-to-br from-primary to-primary/90",
                },
                {
                  icon: (
                    <svg
                      className="h-6 w-6"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  ),
                  title: "Hemat Waktu",
                  description:
                    "Mempercepat proses penyusunan jadwal yang biasanya memakan waktu berhari-hari",
                  bgClass: "bg-gradient-to-br from-secondary to-secondary/90",
                },
                {
                  icon: <Brain className="h-6 w-6" />,
                  title: "Memudahkan Proses Penjadwalan",
                  description:
                    "Jadwal yang dihasilkan meminimalisir modifikasi secara manual oleh satu pihak",
                  bgClass: "bg-gradient-to-br from-primary to-primary/90",
                },
                {
                  icon: <Book className="h-6 w-6" />,
                  title: "Penggunaan Preferensi Dosen",
                  description:
                    "Dosen bisa memilih waktu mengajar berdasarkan preferensi waktu mengajar",
                  bgClass: "bg-gradient-to-br from-secondary to-secondary/90",
                },
              ].map((feature, index) => (
                <div key={index} className="flex items-start">
                  <div className="flex-shrink-0">
                    <div
                      className={`flex items-center justify-center h-12 w-12 rounded-md ${feature.bgClass} text-white shadow-lg`}
                    >
                      {feature.icon}
                    </div>
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-medium text-text-primary font-sans">
                      {feature.title}
                    </h3>
                    <p className="mt-2 text-text-secondary font-sans">
                      {feature.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-16">
            <h2 className="text-2xl font-bold text-text-primary mb-6 font-sans">
              Teknologi yang Kami Gunakan
            </h2>
            <div className="grid md:grid-cols-2 gap-8">
              <div className="bg-gradient-to-br from-surface via-white to-surface p-6 rounded-lg shadow-lg backdrop-blur-sm">
                <h3 className="text-xl font-bold text-text-primary mb-4">
                  Genetic Algorithm (GA)
                </h3>
                <p className="text-text-secondary mb-4">
                  Algoritma Genetika meniru proses evolusi alami untuk menemukan
                  solusi optimal. Dalam konteks penjadwalan, kami menggunakan:
                </p>
                <ul className="space-y-2 text-text-secondary">
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-gradient-to-r from-primary to-primary/70 rounded-full mr-2"></span>
                    Representasi kromosom untuk setiap slot jadwal
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-gradient-to-r from-primary to-primary/70 rounded-full mr-2"></span>
                    Crossover untuk menggabungkan jadwal-jadwal terbaik
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-gradient-to-r from-primary to-primary/70 rounded-full mr-2"></span>
                    Mutasi untuk mengeksplorasi kemungkinan jadwal baru
                  </li>
                </ul>
              </div>

              <div className="bg-gradient-to-br from-surface via-white to-surface p-6 rounded-lg shadow-lg backdrop-blur-sm">
                <h3 className="text-xl font-bold text-text-primary mb-4">
                  Simulated Annealing (SA)
                </h3>
                <p className="text-text-secondary mb-4">
                  Simulated Annealing terinspirasi dari proses pendinginan logam
                  untuk mencapai struktur optimal. Dalam GenPlan, SA berperan
                  untuk:
                </p>
                <ul className="space-y-2 text-text-secondary">
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-gradient-to-r from-secondary to-secondary/70 rounded-full mr-2"></span>
                    Menyempurnakan hasil dari Genetic Algorithm
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-gradient-to-r from-secondary to-secondary/70 rounded-full mr-2"></span>
                    Menghindari solusi lokal optimal
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-gradient-to-r from-secondary to-secondary/70 rounded-full mr-2"></span>
                    Mengoptimalkan penggunaan ruang dan waktu
                  </li>
                </ul>
              </div>
            </div>

            <div className="mt-8 bg-gradient-to-br from-surface via-white to-surface p-6 rounded-lg shadow-lg backdrop-blur-sm">
              <h3 className="text-xl font-bold text-text-primary mb-4">
                Proses Penjadwalan GenPlan
              </h3>
              <div className="space-y-4 text-text-secondary">
                <p>
                  GenPlan mengkombinasikan kekuatan GA dan SA dalam proses tiga
                  tahap:
                </p>
                <ol className="space-y-2">
                  {[
                    "GA menghasilkan populasi jadwal awal dan melakukan evolusi untuk menemukan kandidat jadwal terbaik",
                    "SA mengoptimalkan hasil GA dengan mencoba berbagai variasi kecil dan menerima perubahan yang menghasilkan peningkatan",
                    "Sistem melakukan validasi final untuk memastikan tidak ada konflik jadwal dan semua konstrain terpenuhi",
                  ].map((step, index) => (
                    <li key={index} className="flex items-start">
                      <span className="flex-shrink-0 w-6 h-6 bg-gradient-to-r from-primary to-primary/90 text-primary-foreground rounded-full flex items-center justify-center mr-2 mt-1">
                        {index + 1}
                      </span>
                      <p>{step}</p>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
