# Chạy file này trong terminal: python create_test_audio.py
from gtts import gTTS
 
text = """
Trí tuệ nhân tạo (Artificial Intelligence – AI) đang ngày càng đóng vai trò quan trọng trong nhiều lĩnh vực như y tế, tài chính, giáo dục và công nghiệp. Nhờ khả năng xử lý dữ liệu lớn và học từ kinh nghiệm, AI có thể hỗ trợ con người trong việc ra quyết định, tự động hóa quy trình và tối ưu hóa hiệu suất làm việc. Tuy nhiên, bên cạnh những lợi ích, AI cũng đặt ra nhiều thách thức như vấn đề đạo đức, quyền riêng tư và nguy cơ thay thế lao động con người. Vì vậy, việc ứng dụng AI cần được kiểm soát và phát triển một cách có trách nhiệm.

"""
 
tts = gTTS(text=text, lang="vi")
tts.save("test_audio.mp3")
print("✅ Tạo file test_audio.mp3 thành công!")