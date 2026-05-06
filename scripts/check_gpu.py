import platform
import sys


def main() -> None:
    print(f"Python version: {sys.version.split()[0]} ({platform.python_implementation()})")

    try:
        import torch
    except ImportError:
        print("PyTorch version: not installed")
        print("CUDA availability: False")
        print("CUDA device name: N/A")
        print("CUDA device count: 0")
        return

    print(f"PyTorch version: {torch.__version__}")

    cuda_available = torch.cuda.is_available()
    device_count = torch.cuda.device_count() if cuda_available else 0
    device_name = torch.cuda.get_device_name(0) if cuda_available and device_count > 0 else "N/A"

    print(f"CUDA availability: {cuda_available}")
    print(f"CUDA device name: {device_name}")
    print(f"CUDA device count: {device_count}")


if __name__ == "__main__":
    main()
