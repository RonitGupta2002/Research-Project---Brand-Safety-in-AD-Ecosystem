from PIL import Image
import time
import os


class FullPageScreenshotCollector:
    
    def __init__(self, profile, ss_output_path, ss_output_directory) -> None:
        self.profile = profile
        self.ss_output_path = ss_output_path
        self.ss_output_directory = ss_output_directory
        
    def captureFullScreenshot(self, driver):

        # self.exploreFullPage(driver)
        print("")
        try:
            # total_width = driver.execute_script("return document.body.offsetWidth")
            total_width = 1920
            total_height = driver.execute_script("return document.body.parentNode.scrollHeight")
            # viewport_width = driver.execute_script("return document.body.clientWidth")
            viewport_width = total_width
            viewport_height = driver.execute_script("return window.innerHeight")
            gap_height = 190

            rectangles = []
               
            i = 0
            while i < total_height:
                j = 0
                top_height = i + viewport_height
            
                if top_height > total_height:
                    top_height = total_height
            
                while j < total_width:
                    top_width = j + viewport_width
            
                    if top_width > total_width:
                        top_width = total_width
            
                    rectangles.append((j, i, top_width, top_height))
            
                    j += viewport_width
            
                i += viewport_height
            
            # Calculate the total height with gaps
            total_height_with_gaps = total_height + (gap_height * (len(rectangles) - 1))
            stitched_image = Image.new('RGB', (total_width, total_height_with_gaps))
            previous = None
            part = 0
            
            for rectangle in rectangles:
                if previous is not None:
                    driver.execute_script("window.scrollTo({}, {})".format(rectangle[0], rectangle[1]))
                    time.sleep(0.2)
            
                file_name = "part_{0}.png".format(part)
            
                # Concatenate directory path and file name
                file_path = os.path.join(self.ss_output_directory, file_name)

                driver.get_screenshot_as_file(file_name)
                driver.get_screenshot_as_file(file_path)
                screenshot = Image.open(file_name)
            
                if rectangle[1] + viewport_height > total_height:
                    offset_y = total_height_with_gaps - viewport_height
                else:
                    offset_y = rectangle[1] + (gap_height * part)
                
                offset = (rectangle[0], offset_y)
                stitched_image.paste(screenshot, offset)
                del screenshot
                os.remove(file_name)
                part += 1
                previous = rectangle
            
            stitched_image.save(self.ss_output_path)
     
        except BaseException as e:
            print("[ERROR] captureFullScreenshot()::FullPageScreenshotCollector", e)
        
        return
