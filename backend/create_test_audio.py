# Chạy file này trong terminal: python create_test_audio.py
from gtts import gTTS
 
text = """
Có ai đã thử dùng agentic chunking chưa? Hiện tại mình đang dùng unstructured hi-res để phân tích các file PDF của mình, rồi dùng chức năng "chunk by title" của unstructured để tạo các đoạn văn bản nhỏ. Tuy nhiên, mình vẫn chưa hài lòng lắm vì vẫn phải tự xóa header và footer, và kết quả vẫn chưa được như ý.

Mình đang nghĩ đến việc dùng LLM (Gemini 1.5 pro, vertexai) để làm phần này. Một prompt để lấy metadata (tiêu đề, các mục, số trang và tóm tắt) của tài liệu, rồi yêu cầu một agent khác tạo các đoạn văn bản nhỏ, đồng thời cung cấp cho nó tài liệu, bản tóm tắt cũng như các mục đã trích xuất trước đó để nó có thể gán mỗi đoạn văn bản nhỏ vào một mục. (Điều này sẽ giúp ích cho mình sau này trong quá trình tìm kiếm vì mình có thể lấy được các đoạn văn bản nhỏ xung quanh trong cùng một mục khi truy xuất các đoạn văn bản nhỏ được lưu trữ trong cơ sở dữ liệu Neo4j)

Rất muốn nghe những ý kiến đóng góp về ý tưởng của mình và về bất kỳ kinh nghiệm nào khi sử dụng LLM để chia nhỏ văn bản.

"""
 
tts = gTTS(text=text, lang="vi")
tts.save("test_audio.mp3")
print("✅ Tạo file test_audio.mp3 thành công!")