export default function LoadingSpinner({ message = "불러오는 중..." }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <div className="w-10 h-10 border-4 border-accent border-t-transparent rounded-full animate-spin" />
      <p className="text-neutral text-sm">{message}</p>
    </div>
  );
}