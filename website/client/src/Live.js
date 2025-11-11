import React, { useState, useRef } from "react";
import Webcam from "react-webcam";
import { TabContext, TabPanel, TabList } from '@mui/lab';
import { Box, Tab } from '@mui/material';

const Live = () => {
    const webcamRef = useRef(null);
    const [tabValue, setTabValue] = useState('live')
    const [imgSrc, setImgSrc] = useState(null)
    const [selectedImg, setSelectedImg] = useState(null)
    return (
        <>
            <TabContext value={tabValue}>
                <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                    <TabList onChange={(e, val) => setTabValue(val)} aria-label="lab API tabs example">
                    <Tab label="Live Camera" value="live" />
                    <Tab label="Upload Image" value="upload" />
                    </TabList>
                </Box>
                <TabPanel value="live">
                    <Webcam
                        ref={webcamRef}
                        screenshotFormat="image/jpeg"
                        mirrored={true}
                    >
                        {({ getScreenshot }) => (
                        <button
                            onClick={() => {
                                setImgSrc(getScreenshot())
                            }}
                        >
                            Capture photo
                        </button>
                        )}
                    </Webcam>

                    {imgSrc && (
                        <img
                        src={imgSrc}
                        />
                    )}
                </TabPanel>
                <TabPanel value="upload">
                    <input
                        type="file"
                        onChange={(e) => {
                            setSelectedImg(e.target.files[0])
                        }}
                    />
                    {selectedImg && (
                        <img
                            src={URL.createObjectURL(selectedImg)}
                        />
                    )}
                </TabPanel>
            </TabContext>

            
            
        </>
    )
}

export default Live