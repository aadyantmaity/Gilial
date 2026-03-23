import { ArrowRight } from "lucide-react";

export function InteractiveHoverButton({
  children,
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={`group relative inline-flex items-center justify-center rounded-full border border-teal-600 bg-teal-600 px-6 py-3 font-semibold text-black overflow-hidden ${className || ""}`}
      {...props}
    >
      {/* Original text */}
      <span className="inline-flex items-center gap-2 transition-all duration-300 group-hover:translate-x-12 group-hover:opacity-0 ease-out">
        {children}
      </span>

      {/* Arrow version */}
      <div className="absolute inline-flex items-center gap-2 translate-x-12 opacity-0 transition-all duration-300 group-hover:translate-x-0 group-hover:opacity-100 ease-out">
        <span>{children}</span>
        <ArrowRight size={18} />
      </div>
    </button>
  );
}
