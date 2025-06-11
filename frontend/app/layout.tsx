import "@livekit/components-styles";
import "./globals.css";
import { Public_Sans } from "next/font/google";
import Image from 'next/image';

const publicSans400 = Public_Sans({
  weight: "400",
  subsets: ["latin"],
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`h-full ${publicSans400.className}`}>
      <body className="h-full bg-white relative">
        <div className="absolute top-6 left-6 z-10">
          <Image 
            src="/images/LogoGovlab.jpg"
            alt="Logo GovLab" 
            width={120}
            height={45}
            priority
          />
        </div>
        <div className="absolute top-6 right-6 z-10">
          <Image 
            src="/images/logo.jpg"
            alt="Logo Universidad de la Sabana" 
            width={120}
            height={45}
            priority
          />
        </div>
        {children}
      </body>
    </html>
  );
}