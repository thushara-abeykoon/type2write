import React from 'react'

const ErrorAlert = ({alertInfo, setIsActive}) => {
    const handleClick = () => {
        setIsActive(false);
    }
  return (
    <div className='w-[100vw] h-[100vh] fixed right-0 top-0 backdrop-blur-sm flex justify-center items-center'>
        <div className='px-10 py-5 rounded-md bg-white backdrop-blur-sm flex flex-col justify-center gap-10 items-center'>
            <p className='text-red-500'>{alertInfo}</p>
            <button className='transition-all duration-300 w-full bg-red-400 py-2 rounded-md hover:bg-red-500' onClick={handleClick}>OK</button>
        </div>
    </div>
  )
}

export default ErrorAlert