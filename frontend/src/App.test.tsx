import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

const usuario = {
  id: 1, nombre: 'Raúl Tello', email: 'raul@cafe.pe',
  organizacion: { id: 1, tipo: 'TOSTADOR', nombre: 'Tostaduría Raúl', ruc: null, region: null },
};

beforeEach(() => { sessionStorage.clear(); jest.clearAllMocks(); });

test('registro de cooperativa con invitación vigente inicia sesión', async () => {
  const cooperativa = { ...usuario, organizacion: { ...usuario.organizacion, tipo: 'PROVEEDOR' } };
  globalThis.fetch = jest.fn().mockImplementation(async (url: string) => ({
    ok: true, status: url.endsWith('/registro-invitacion') ? 201 : 200,
    json: async () => url.endsWith('/invitaciones/token-valido')
      ? { tostador: 'Tostadora Uno', proveedor: 'Cooperativa Jaén', vigente: true, expira_en: new Date().toISOString() }
      : url.endsWith('/registro-invitacion')
        ? { access_token: 'coop.jwt', token_type: 'bearer', usuario: cooperativa }
        : { status: 'ok', environment: 'test', app: 'Origin Link' },
  })) as jest.Mock;
  render(<MemoryRouter initialEntries={['/invitacion/token-valido']}><App /></MemoryRouter>);
  expect(await screen.findByRole('heading', { name: /invitación a origin link/i })).toBeInTheDocument();
  await screen.findByRole('button', { name: /registrarme y aceptar invitación/i });
  fireEvent.change(screen.getByLabelText(/nombre del responsable/i), { target: { value: 'Ana Pérez' } });
  fireEvent.change(screen.getByLabelText(/correo electrónico/i), { target: { value: 'ana@coop.pe' } });
  fireEvent.change(screen.getByLabelText(/contraseña \(mínimo/i), { target: { value: 'ClaveSegura123' } });
  fireEvent.click(screen.getByRole('button', { name: /registrarme y aceptar invitación/i }));
  expect(await screen.findByRole('heading', { name: /panel de cooperativa/i })).toBeInTheDocument();
  expect(sessionStorage.getItem('originlink_access_token')).toBe('coop.jwt');
});


test('ruta privada exige sesión', async () => {
  globalThis.fetch = jest.fn() as jest.Mock;
  render(<MemoryRouter initialEntries={['/']}><App /></MemoryRouter>);
  expect(await screen.findByRole('heading', { name: /iniciar sesión/i })).toBeInTheDocument();
});

test('registro guarda token y dirige al panel; logout bloquea el acceso', async () => {
  globalThis.fetch = jest.fn().mockImplementation(async (url: string) => ({
    ok: true, status: 201,
    json: async () => url.endsWith('/registro')
      ? { access_token: 'test.jwt.token', token_type: 'bearer', usuario }
      : { status: 'ok', environment: 'test', app: 'Origin Link' },
  })) as jest.Mock;
  render(<MemoryRouter initialEntries={['/registro']}><App /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText(/nombre de la empresa/i), { target: { value: 'Tostaduría Raúl' } });
  fireEvent.change(screen.getByLabelText(/nombre del responsable/i), { target: { value: 'Raúl Tello' } });
  fireEvent.change(screen.getByLabelText(/correo electrónico/i), { target: { value: 'raul@cafe.pe' } });
  fireEvent.change(screen.getByLabelText(/contraseña \(mínimo/i), { target: { value: 'ClaveSegura123' } });
  fireEvent.click(screen.getByRole('button', { name: 'Crear cuenta' }));
  expect(await screen.findByRole('heading', { name: /panel del tostador/i })).toBeInTheDocument();
  expect(sessionStorage.getItem('originlink_access_token')).toBe('test.jwt.token');
  fireEvent.click(screen.getByRole('button', { name: /cerrar sesión/i }));
  await waitFor(() => expect(screen.getByRole('heading', { name: /iniciar sesión/i })).toBeInTheDocument());
  expect(sessionStorage.getItem('originlink_access_token')).toBeNull();
});

test('muestra el mensaje del servidor ante correo duplicado', async () => {
  globalThis.fetch = jest.fn().mockResolvedValue({ ok: false, status: 409,
    json: async () => ({ detail: 'Ya existe una cuenta con este correo' }) }) as jest.Mock;
  render(<MemoryRouter initialEntries={['/registro']}><App /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText(/nombre de la empresa/i), { target: { value: 'Tostaduría Raúl' } });
  fireEvent.change(screen.getByLabelText(/nombre del responsable/i), { target: { value: 'Raúl Tello' } });
  fireEvent.change(screen.getByLabelText(/correo electrónico/i), { target: { value: 'raul@cafe.pe' } });
  fireEvent.change(screen.getByLabelText(/contraseña \(mínimo/i), { target: { value: 'ClaveSegura123' } });
  fireEvent.click(screen.getByRole('button', { name: 'Crear cuenta' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Ya existe una cuenta con este correo');
});


test('login con credenciales incorrectas muestra error genérico', async () => {
  globalThis.fetch = jest.fn().mockResolvedValue({ ok: false, status: 401,
    json: async () => ({ detail: 'Correo o contraseña incorrectos' }) }) as jest.Mock;
  render(<MemoryRouter initialEntries={['/login']}><App /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText(/correo electrónico/i), { target: { value: 'error@cafe.pe' } });
  fireEvent.change(screen.getByLabelText(/^contraseña$/i), { target: { value: 'incorrecta' } });
  fireEvent.click(screen.getByRole('button', { name: /^ingresar$/i }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Correo o contraseña incorrectos');
});

test('login de cooperativa muestra su panel y no muestra opciones exclusivas del tostador', async () => {
  const cooperativa = { ...usuario, organizacion: { ...usuario.organizacion, tipo: 'PROVEEDOR' } };
  globalThis.fetch = jest.fn().mockImplementation(async (url: string) => ({
    ok: true, status: 200,
    json: async () => url.endsWith('/login')
      ? { access_token: 'cooperativa.jwt', token_type: 'bearer', usuario: cooperativa }
      : { status: 'ok', environment: 'test', app: 'Origin Link' },
  })) as jest.Mock;
  render(<MemoryRouter initialEntries={['/login']}><App /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText(/correo electrónico/i), { target: { value: 'cooperativa@cafe.pe' } });
  fireEvent.change(screen.getByLabelText(/^contraseña$/i), { target: { value: 'ClaveSegura123' } });
  fireEvent.click(screen.getByRole('button', { name: /^ingresar$/i }));
  expect(await screen.findByRole('heading', { name: /panel de cooperativa/i })).toBeInTheDocument();
  expect(screen.queryByRole('link', { name: 'Compras' })).not.toBeInTheDocument();
});
