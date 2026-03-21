export default function ErrorMessage({ message }) {
  return (
    <div className="bg-red-900/30 border border-bear rounded-lg px-4 py-3 text-bear text-sm">
      ⚠️ {message}
    </div>
  );
}