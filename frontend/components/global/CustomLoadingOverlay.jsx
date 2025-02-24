export const LoadingOverlay = ({ active, text, children }) => {
  return (
    <div className="relative">
      {children}
      {active && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-800 bg-opacity-50 z-50">
          <div className="animate-spin rounded-full border-t-4 border-b-4 border-white h-8 w-8" />
          <p className="mt-2 text-white">{text}</p>
        </div>
      )}
    </div>
  );
};
