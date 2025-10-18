import React from 'react';
import { useNavigate } from 'react-router-dom';


const Index = () => {
    const Navigate = useNavigate();
    
    return (
        <div className='min-h-screen bg-gradient-to-br from-primary-50 to-secondary-100'>
            <header className="flex justify-between items-center bg-white py-4 px-6 shadow-md">
            <h1 className='text-2xl font-bold'>InfoClass</h1>
            <nav className="flex gap-4 justify-center aling-center">
                <a href="">Caracteristicas</a>
                <a href="">Testimonios</a>
                <a href="">Precios</a>
            </nav>
            <div className="flex gap-4">
                <button onClick={() => Navigate('/login')} className=" px-4 py-2 rounded-md">Iniciar Sesión</button>
                <button onClick={() => Navigate('/register')} className="bg-primary-600 text-white px-4 py-2 rounded-md font-bold ">Registrarse</button>
            </div>
            </header>
            <main>
                <section className="flex flex-col items-center justify-center py-20">
                    <h1 className='text-6xl font-bold text-center max-w-4xl'>Gestiona tus cursos de forma <strong className="text-primary-600">inteligente</strong>.</h1>
                    <p className='text-xl text-secondary-600 text-center max-w-3xl py-4'>La plataforma todo en uno para estudiantes y educadores. Organiza tus cursos, tareas y comunicacion en un solo lugar.</p>
                    <button className='bg-primary-600 text-white font-bold rounded-md px-8 py-4'>Comienza ahora</button>
                </section>
                <section className='bg-white flex flex-col items-center justify-center py-20'>
                    <h1 className="text-4xl font-bold text-center">Todo lo que necesitas para tener éxito</h1>
                    <p className="text-secondary-600 text-center max-w-3xl py-4">Descubre las herramientes que te ayudarán a potenciar tu aprendizaje. </p>
                    <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 w-full max-w-7xl mx-auto'>
                        <div className='py-12 text-center'>
                            <div className='flex items-center justify-center h-16 w-16 rounded-full bg-primary-100 mx-auto mb-4'>
                                <img src="icons/book.svg" alt="Gestión de Cursos" className='w-10 h-10' /> 
                            </div> 
                            <h2 className='text-2xl font-bold'>Gestión de Cursos</h2>
                            <p className='text-secondary-600 text-center max-w-xs mx-auto py-2'>Mantén todos tus materiales, notas y calendarios de cursos organizados en un solo lugar.</p>
                        </div>
                        <div className='py-12 text-center'>
                            <div className='flex items-center justify-center h-16 w-16 rounded-full bg-primary-100 mx-auto mb-4'>
                                <img src="icons/files-check.svg" alt="Seguimiento de Tareas" className='w-10 h-10' /> 
                            </div>
                            <h2 className='text-2xl font-bold'>Seguimiento de Tareas</h2>
                            <p className='text-secondary-600 text-center max-w-xs mx-auto py-2'>Nunca más olvides una fecha de entrega. Recibe recordatorios y visualiza tu progreso.</p>
                        </div>
                        <div className='py-12 text-center'>
                            <div className='flex items-center justify-center h-16 w-16 rounded-full bg-primary-100 mx-auto mb-4'>
                                <img src="icons/message.svg" alt="Comunicación" className='w-10 h-10' /> 
                            </div>
                            <h2 className='text-2xl font-bold'>Mensajería Integrada</h2>
                            <p className='text-secondary-600 text-center max-w-xs mx-auto py-2'>Comunicate facilmente con tus profesores y compañeros de clases sin salir de la plataforma.</p>
                        </div>
                    </div>
                </section>
                <section className='flex flex-col items-center justify-center py-20'>
                    <h1 className='text-4xl font-bold text-center'>Lo que dicen nuestros usuarios</h1>
                    <p className='text-xl text-secondary-600 text-center max-w-3xl py-4 font-bold'>Miles de estudiantes y educadores aman InfoClass.</p>
                </section>
                <section className='bg-primary-600 flex flex-col items-center justify-center py-20 text-white'>
                    <h1 className='text-4xl font-bold text-center'>¿Listo para llevar tu educación al proximo nivel?</h1>
                    <p className='text-secundary-600 text-center max-w-3xl max-h-96 py-8'>Unete a la comunidad de InfoClass Hoy mismo. Es gratis para empezar. </p>
                    <button onClick={() => Navigate('/register')} className='bg-white text-primary-600 px-4 py-2 rounded-md font-bold'>Crear mi cuenta</button>
                </section>
            </main>
        </div>
    )
}


export default Index;